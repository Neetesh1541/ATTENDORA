from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, time, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    AttendanceSession,
    AttendanceRecord,
    AttendanceStatus,
    AttendanceAction,
    Person,
    PersonStatus,
    Department,
    Shift,
    Camera,
    User,
    UserRole,
    utcnow,
)
from app.schemas.schemas import (
    AttendanceSessionCreate,
    AttendanceSessionUpdate,
    AttendanceSessionResponse,
    AttendanceSessionListResponse,
    AttendanceRecordCreate,
    AttendanceRecordUpdate,
    AttendanceRecordResponse,
    AttendanceRecordListResponse,
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceMarkRequest,
    TodaySummaryResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}/attendance", tags=["Attendance"])


def parse_time_str(time_str: str) -> Optional[time]:
    try:
        parts = [int(p) for p in time_str.split(":")]
        return time(hour=parts[0], minute=parts[1])
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ATTENDANCE SESSIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/sessions", response_model=AttendanceSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    org_id: UUID,
    req: AttendanceSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    session = AttendanceSession(
        organization_id=org_id,
        name=req.name.strip(),
        session_date=req.session_date,
        start_time=req.start_time,
        end_time=req.end_time,
        session_type=req.session_type or "general",
        department_id=req.department_id,
        team_id=req.team_id,
        shift_id=req.shift_id,
        camera_id=req.camera_id,
        is_active=req.is_active if req.is_active is not None else True,
        created_by=current_user.id,
    )
    db.add(session)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_attendance_session",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="AttendanceSession",
        resource_id=str(session.id),
        details={"name": session.name, "date": str(session.session_date)},
    )

    resp = AttendanceSessionResponse.model_validate(session)
    resp.record_count = 0
    return resp


@router.get("/sessions", response_model=AttendanceSessionListResponse)
async def list_sessions(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session_date: Optional[date] = Query(None),
    session_type: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(AttendanceSession).where(AttendanceSession.organization_id == org_id)
    count_query = select(func.count(AttendanceSession.id)).where(AttendanceSession.organization_id == org_id)

    filters = []
    if session_date:
        filters.append(AttendanceSession.session_date == session_date)
    if session_type:
        filters.append(AttendanceSession.session_type == session_type)
    if department_id:
        filters.append(AttendanceSession.department_id == department_id)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(AttendanceSession.session_date.desc(), AttendanceSession.created_at.desc()).offset(skip).limit(limit))
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        cnt = await db.scalar(
            select(func.count(AttendanceRecord.id)).where(AttendanceRecord.session_id == s.id)
        ) or 0
        resp = AttendanceSessionResponse.model_validate(s)
        resp.record_count = cnt
        items.append(resp)

    return AttendanceSessionListResponse(total=total, items=items)


# ═══════════════════════════════════════════════════════════════════════════
# CHECK-IN / CHECK-OUT / MARK MANUAL
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/check-in", response_model=AttendanceRecordResponse)
async def check_in(
    org_id: UUID,
    req: AttendanceCheckInRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    # Validate person
    person_res = await db.execute(
        select(Person).where(Person.id == req.person_id, Person.organization_id == org_id)
    )
    person = person_res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    now = req.check_in_time or utcnow()
    today_dt = now.date() if isinstance(now, datetime) else now

    # Check existing record for today
    rec_res = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.person_id == req.person_id,
            AttendanceRecord.date == today_dt,
        )
    )
    record = rec_res.scalar_one_or_none()

    if record and record.check_in_time is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person is already checked in at {record.check_in_time.strftime('%H:%M:%S')}",
        )

    # Check shift timing to determine late arrival
    is_late = False
    late_minutes = 0
    if person.shift_id:
        shift_res = await db.execute(select(Shift).where(Shift.id == person.shift_id))
        shift = shift_res.scalar_one_or_none()
        if shift and shift.start_time:
            s_time = parse_time_str(shift.start_time)
            if s_time:
                check_in_tod = now.time()
                shift_mins = s_time.hour * 60 + s_time.minute + (shift.grace_period_minutes or 0)
                actual_mins = check_in_tod.hour * 60 + check_in_tod.minute
                if actual_mins > shift_mins:
                    is_late = True
                    late_minutes = actual_mins - (s_time.hour * 60 + s_time.minute)

    status_val = AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT

    if record is None:
        record = AttendanceRecord(
            organization_id=org_id,
            person_id=req.person_id,
            session_id=req.session_id,
            date=today_dt,
            status=status_val,
            action=AttendanceAction.CHECK_IN,
            check_in_time=now,
            is_late=is_late,
            late_minutes=late_minutes,
            camera_id=req.camera_id,
            marked_by="manual",
            notes=req.notes,
        )
        db.add(record)
    else:
        record.check_in_time = now
        record.action = AttendanceAction.CHECK_IN
        record.status = status_val
        record.is_late = is_late
        record.late_minutes = late_minutes
        if req.session_id:
            record.session_id = req.session_id
        if req.camera_id:
            record.camera_id = req.camera_id
        if req.notes:
            record.notes = (record.notes + "\n" + req.notes) if record.notes else req.notes

    await db.flush()

    resp = AttendanceRecordResponse.model_validate(record)
    resp.person_name = person.full_name
    resp.person_unique_id = person.unique_id
    return resp


@router.post("/check-out", response_model=AttendanceRecordResponse)
async def check_out(
    org_id: UUID,
    req: AttendanceCheckOutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    person_res = await db.execute(
        select(Person).where(Person.id == req.person_id, Person.organization_id == org_id)
    )
    person = person_res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    now = req.check_out_time or utcnow()
    today_dt = now.date() if isinstance(now, datetime) else now

    rec_res = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.person_id == req.person_id,
            AttendanceRecord.date == today_dt,
        )
    )
    record = rec_res.scalar_one_or_none()

    if not record or not record.check_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check out: no active check-in found for today",
        )

    if record.check_out_time is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person is already checked out",
        )

    record.check_out_time = now
    record.action = AttendanceAction.CHECK_OUT

    # Calculate total hours
    diff_secs = (record.check_out_time - record.check_in_time).total_seconds()
    record.total_hours = round(max(0.0, diff_secs / 3600.0), 2)

    # Check early departure against shift
    if person.shift_id:
        shift_res = await db.execute(select(Shift).where(Shift.id == person.shift_id))
        shift = shift_res.scalar_one_or_none()
        if shift and shift.end_time:
            end_t = parse_time_str(shift.end_time)
            if end_t:
                scheduled_end_mins = end_t.hour * 60 + end_t.minute
                actual_end_mins = now.time().hour * 60 + now.time().minute
                if actual_end_mins < scheduled_end_mins:
                    record.is_early_departure = True
                    record.early_departure_minutes = scheduled_end_mins - actual_end_mins
                elif actual_end_mins > scheduled_end_mins:
                    record.overtime_minutes = actual_end_mins - scheduled_end_mins

    if req.notes:
        record.notes = (record.notes + "\n" + req.notes) if record.notes else req.notes

    record.updated_at = utcnow()
    await db.flush()

    resp = AttendanceRecordResponse.model_validate(record)
    resp.person_name = person.full_name
    resp.person_unique_id = person.unique_id
    return resp


@router.post("/mark", response_model=AttendanceRecordResponse)
async def mark_attendance(
    org_id: UUID,
    req: AttendanceMarkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    person_res = await db.execute(
        select(Person).where(Person.id == req.person_id, Person.organization_id == org_id)
    )
    person = person_res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    rec_res = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.person_id == req.person_id,
            AttendanceRecord.date == req.date,
        )
    )
    record = rec_res.scalar_one_or_none()

    total_hours = None
    if req.check_in_time and req.check_out_time:
        total_hours = round(max(0.0, (req.check_out_time - req.check_in_time).total_seconds() / 3600.0), 2)

    if record is None:
        record = AttendanceRecord(
            organization_id=org_id,
            person_id=req.person_id,
            session_id=req.session_id,
            date=req.date,
            status=req.status,
            check_in_time=req.check_in_time,
            check_out_time=req.check_out_time,
            total_hours=total_hours,
            is_late=req.is_late or False,
            late_minutes=req.late_minutes or 0,
            marked_by="manual",
            notes=req.notes,
        )
        db.add(record)
    else:
        record.status = req.status
        if req.session_id is not None:
            record.session_id = req.session_id
        if req.check_in_time is not None:
            record.check_in_time = req.check_in_time
        if req.check_out_time is not None:
            record.check_out_time = req.check_out_time
        if total_hours is not None:
            record.total_hours = total_hours
        if req.is_late is not None:
            record.is_late = req.is_late
        if req.late_minutes is not None:
            record.late_minutes = req.late_minutes
        if req.notes is not None:
            record.notes = req.notes
        record.updated_at = utcnow()

    await db.flush()

    await log_audit_event(
        db=db,
        action="mark_attendance_manual",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="AttendanceRecord",
        resource_id=str(record.id),
        details={"person_id": str(person.id), "status": req.status.value, "date": str(req.date)},
    )

    resp = AttendanceRecordResponse.model_validate(record)
    resp.person_name = person.full_name
    resp.person_unique_id = person.unique_id
    return resp


# ═══════════════════════════════════════════════════════════════════════════
# RECORDS & TODAY SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/records", response_model=AttendanceRecordListResponse)
async def get_attendance_records(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    person_id: Optional[UUID] = Query(None),
    department_id: Optional[UUID] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    session_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = (
        select(AttendanceRecord, Person, Department.name.label("department_name"))
        .join(Person, AttendanceRecord.person_id == Person.id)
        .outerjoin(Department, Person.department_id == Department.id)
        .where(AttendanceRecord.organization_id == org_id)
    )
    count_query = (
        select(func.count(AttendanceRecord.id))
        .join(Person, AttendanceRecord.person_id == Person.id)
        .where(AttendanceRecord.organization_id == org_id)
    )

    filters = []
    if start_date:
        filters.append(AttendanceRecord.date >= start_date)
    if end_date:
        filters.append(AttendanceRecord.date <= end_date)
    if person_id:
        filters.append(AttendanceRecord.person_id == person_id)
    if status:
        filters.append(AttendanceRecord.status == status)
    if session_id:
        filters.append(AttendanceRecord.session_id == session_id)
    if department_id:
        filters.append(Person.department_id == department_id)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(
        query.order_by(AttendanceRecord.date.desc(), AttendanceRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    items = []
    for rec, person, dept_name in rows:
        resp = AttendanceRecordResponse.model_validate(rec)
        resp.person_name = person.full_name
        resp.person_unique_id = person.unique_id
        resp.department_name = dept_name
        items.append(resp)

    return AttendanceRecordListResponse(total=total, items=items)


@router.get("/today", response_model=TodaySummaryResponse)
async def get_today_attendance_summary(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    today = date.today()

    total_people = await db.scalar(
        select(func.count(Person.id)).where(
            Person.organization_id == org_id,
            Person.status == PersonStatus.ACTIVE,
        )
    ) or 0

    records_res = await db.execute(
        select(AttendanceRecord, Person, Department.name.label("department_name"))
        .join(Person, AttendanceRecord.person_id == Person.id)
        .outerjoin(Department, Person.department_id == Department.id)
        .where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
        )
        .order_by(AttendanceRecord.updated_at.desc())
    )
    rows = records_res.all()

    present_count = 0
    late_count = 0
    half_day_count = 0
    leave_count = 0

    recent_records = []
    for rec, person, dept_name in rows:
        if rec.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
            present_count += 1
        if rec.status == AttendanceStatus.LATE or rec.is_late:
            late_count += 1
        if rec.status == AttendanceStatus.HALF_DAY:
            half_day_count += 1
        if rec.status == AttendanceStatus.LEAVE:
            leave_count += 1

        if len(recent_records) < 20:
            resp = AttendanceRecordResponse.model_validate(rec)
            resp.person_name = person.full_name
            resp.person_unique_id = person.unique_id
            resp.department_name = dept_name
            recent_records.append(resp)

    absent_count = max(0, total_people - present_count - leave_count)
    rate = round((present_count / total_people * 100), 2) if total_people > 0 else 0.0

    return TodaySummaryResponse(
        date=today,
        total_people=total_people,
        present=present_count,
        absent=absent_count,
        late=late_count,
        half_day=half_day_count,
        on_leave=leave_count,
        attendance_percentage=rate,
        recent_records=recent_records,
    )
