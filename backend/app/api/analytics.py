from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    Person,
    PersonStatus,
    AttendanceRecord,
    AttendanceStatus,
    AttendanceCorrection,
    CorrectionStatus,
    Department,
    Shift,
    Camera,
    CameraStatus,
    RecognitionLog,
    User,
)
from app.schemas.schemas import (
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
    DailyTrendItem,
    DepartmentAnalyticsItem,
    ShiftAnalyticsItem,
    CameraAnalyticsItem,
)

router = APIRouter(prefix="/api/organizations/{org_id}/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    today = date.today()

    total_members = await db.scalar(
        select(func.count(Person.id)).where(
            Person.organization_id == org_id,
            Person.status == PersonStatus.ACTIVE,
        )
    ) or 0

    present_today = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]),
        )
    ) or 0

    late_today = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
            AttendanceRecord.is_late.is_(True),
        )
    ) or 0

    on_leave_today = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
            AttendanceRecord.status == AttendanceStatus.LEAVE,
        )
    ) or 0

    absent_today = max(0, total_members - present_today - on_leave_today)
    att_pct = round((present_today / total_members * 100), 2) if total_members > 0 else 0.0

    total_cameras = await db.scalar(
        select(func.count(Camera.id)).where(
            Camera.organization_id == org_id,
            Camera.is_active.is_(True),
        )
    ) or 0

    active_cameras = await db.scalar(
        select(func.count(Camera.id)).where(
            Camera.organization_id == org_id,
            Camera.is_active.is_(True),
            Camera.status == CameraStatus.ONLINE,
        )
    ) or 0

    pending_corrections = await db.scalar(
        select(func.count(AttendanceCorrection.id)).where(
            AttendanceCorrection.organization_id == org_id,
            AttendanceCorrection.status == CorrectionStatus.PENDING,
        )
    ) or 0

    return AnalyticsOverviewResponse(
        total_members=total_members,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        on_leave_today=on_leave_today,
        attendance_percentage=att_pct,
        active_cameras=active_cameras,
        total_cameras=total_cameras,
        pending_corrections=pending_corrections,
    )


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_analytics_trends(
    org_id: UUID,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    total_members = await db.scalar(
        select(func.count(Person.id)).where(
            Person.organization_id == org_id,
            Person.status == PersonStatus.ACTIVE,
        )
    ) or 0

    start_date = date.today() - timedelta(days=days - 1)
    end_date = date.today()

    rec_res = await db.execute(
        select(AttendanceRecord.date, AttendanceRecord.status, AttendanceRecord.is_late)
        .where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
        )
    )
    records = rec_res.all()

    # Aggregate by date
    date_map = {}
    curr = start_date
    while curr <= end_date:
        date_map[curr] = {"present": 0, "absent": 0, "late": 0, "leave": 0}
        curr += timedelta(days=1)

    for r_date, r_status, is_late in records:
        if r_date in date_map:
            if r_status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
                date_map[r_date]["present"] += 1
            if is_late or r_status == AttendanceStatus.LATE:
                date_map[r_date]["late"] += 1
            if r_status == AttendanceStatus.LEAVE:
                date_map[r_date]["leave"] += 1

    trends = []
    for d, counts in sorted(date_map.items()):
        p = counts["present"]
        l = counts["late"]
        lv = counts["leave"]
        ab = max(0, total_members - p - lv)
        rate = round((p / total_members * 100), 2) if total_members > 0 else 0.0
        trends.append(DailyTrendItem(
            date=d.isoformat(),
            present=p,
            absent=ab,
            late=l,
            attendance_rate=rate,
        ))

    return AnalyticsTrendsResponse(trends=trends)


@router.get("/department-wise", response_model=List[DepartmentAnalyticsItem])
async def get_department_analytics(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    today = date.today()

    dept_res = await db.execute(
        select(Department).where(Department.organization_id == org_id, Department.is_active.is_(True))
    )
    departments = dept_res.scalars().all()

    items = []
    for dept in departments:
        members_count = await db.scalar(
            select(func.count(Person.id)).where(
                Person.department_id == dept.id,
                Person.status == PersonStatus.ACTIVE,
            )
        ) or 0

        present_count = await db.scalar(
            select(func.count(AttendanceRecord.id))
            .join(Person, AttendanceRecord.person_id == Person.id)
            .where(
                Person.department_id == dept.id,
                AttendanceRecord.date == today,
                AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]),
            )
        ) or 0

        absent_count = max(0, members_count - present_count)
        rate = round((present_count / members_count * 100), 2) if members_count > 0 else 0.0

        items.append(DepartmentAnalyticsItem(
            department_id=dept.id,
            department_name=dept.name,
            total_members=members_count,
            present=present_count,
            absent=absent_count,
            attendance_rate=rate,
        ))

    return items


@router.get("/shift-wise", response_model=List[ShiftAnalyticsItem])
async def get_shift_analytics(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    today = date.today()

    shift_res = await db.execute(
        select(Shift).where(Shift.organization_id == org_id, Shift.is_active.is_(True))
    )
    shifts = shift_res.scalars().all()

    items = []
    for s in shifts:
        assigned_count = await db.scalar(
            select(func.count(Person.id)).where(
                Person.shift_id == s.id,
                Person.status == PersonStatus.ACTIVE,
            )
        ) or 0

        records_res = await db.execute(
            select(AttendanceRecord.is_late, AttendanceRecord.status)
            .join(Person, AttendanceRecord.person_id == Person.id)
            .where(
                Person.shift_id == s.id,
                AttendanceRecord.date == today,
            )
        )
        records = records_res.all()

        on_time = 0
        late = 0
        present_cnt = 0
        for is_late, status in records:
            if status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
                present_cnt += 1
                if is_late or status == AttendanceStatus.LATE:
                    late += 1
                else:
                    on_time += 1

        absent = max(0, assigned_count - present_cnt)

        items.append(ShiftAnalyticsItem(
            shift_id=s.id,
            shift_name=s.name,
            total_assigned=assigned_count,
            on_time=on_time,
            late=late,
            absent=absent,
        ))

    return items


@router.get("/camera-wise", response_model=List[CameraAnalyticsItem])
async def get_camera_analytics(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    cam_res = await db.execute(
        select(Camera).where(Camera.organization_id == org_id, Camera.is_active.is_(True))
    )
    cameras = cam_res.scalars().all()

    items = []
    for cam in cameras:
        # Check recognition logs if any
        log_res = await db.execute(
            select(
                func.count(RecognitionLog.id),
                func.sum(func.case((RecognitionLog.recognized.is_(True), 1), else_=0))
            ).where(RecognitionLog.camera_id == cam.id)
        )
        row = log_res.first()
        total_det = row[0] or 0
        total_rec = row[1] or 0

        # If no recognition logs, fall back to attendance records marked with this camera
        if total_det == 0:
            rec_cnt = await db.scalar(
                select(func.count(AttendanceRecord.id)).where(AttendanceRecord.camera_id == cam.id)
            ) or 0
            total_det = rec_cnt
            total_rec = rec_cnt

        acc_rate = round((total_rec / total_det * 100), 2) if total_det > 0 else 100.0

        items.append(CameraAnalyticsItem(
            camera_id=cam.id,
            camera_name=cam.name,
            location=cam.location,
            status=cam.status,
            total_detections=total_det,
            total_recognized=total_rec,
            accuracy_rate=acc_rate,
        ))

    return items
