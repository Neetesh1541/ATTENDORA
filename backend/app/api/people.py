import io
import csv
from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    Person,
    PersonStatus,
    FaceRegStatus,
    Department,
    Team,
    Designation,
    Shift,
    AttendanceRecord,
    User,
    UserRole,
    utcnow,
)
from app.schemas.schemas import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonListResponse,
    PersonBulkImportRequest,
    PersonBulkImportResponse,
    AttendanceRecordResponse,
    AttendanceRecordListResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}/people", tags=["People"])


def serialize_person(person: Person) -> PersonResponse:
    resp = PersonResponse.model_validate(person)
    if person.department:
        resp.department_name = person.department.name
    if person.team:
        resp.team_name = person.team.name
    if person.designation_id and hasattr(person, "_designation_name"):
        resp.designation_name = person._designation_name
    return resp


@router.get("", response_model=PersonListResponse)
async def list_people(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[UUID] = Query(None),
    team_id: Optional[UUID] = Query(None),
    status: Optional[PersonStatus] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = (
        select(Person)
        .options(
            selectinload(Person.department),
            selectinload(Person.team),
        )
        .where(Person.organization_id == org_id)
    )
    count_query = select(func.count(Person.id)).where(Person.organization_id == org_id)

    filters = []
    if department_id is not None:
        filters.append(Person.department_id == department_id)
    if team_id is not None:
        filters.append(Person.team_id == team_id)
    if status is not None:
        filters.append(Person.status == status)
    if category is not None:
        filters.append(Person.category == category)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(
            Person.full_name.ilike(search_pattern)
            | Person.unique_id.ilike(search_pattern)
            | Person.email.ilike(search_pattern)
            | Person.phone.ilike(search_pattern)
        )

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Person.full_name.asc()).offset(skip).limit(limit))
    people = result.scalars().all()

    # Pre-fetch designations & shifts for these people for display names
    desig_ids = {p.designation_id for p in people if p.designation_id}
    shift_ids = {p.shift_id for p in people if p.shift_id}

    desig_map = {}
    if desig_ids:
        d_res = await db.execute(select(Designation).where(Designation.id.in_(desig_ids)))
        desig_map = {d.id: d.name for d in d_res.scalars().all()}

    shift_map = {}
    if shift_ids:
        s_res = await db.execute(select(Shift).where(Shift.id.in_(shift_ids)))
        shift_map = {s.id: s.name for s in s_res.scalars().all()}

    items = []
    for p in people:
        resp = PersonResponse.model_validate(p)
        if p.department:
            resp.department_name = p.department.name
        if p.team:
            resp.team_name = p.team.name
        if p.designation_id in desig_map:
            resp.designation_name = desig_map[p.designation_id]
        if p.shift_id in shift_map:
            resp.shift_name = shift_map[p.shift_id]
        items.append(resp)

    return PersonListResponse(total=total, items=items)


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    org_id: UUID,
    req: PersonCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    # Check unique_id
    existing = await db.execute(
        select(Person).where(Person.organization_id == org_id, Person.unique_id == req.unique_id.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID/Code '{req.unique_id}' already exists in this organization",
        )

    # Validate foreign keys within org
    if req.department_id:
        d_check = await db.execute(
            select(Department).where(Department.id == req.department_id, Department.organization_id == org_id)
        )
        if not d_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")

    if req.team_id:
        t_check = await db.execute(
            select(Team).where(Team.id == req.team_id, Team.organization_id == org_id)
        )
        if not t_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid team ID")

    if req.designation_id:
        des_check = await db.execute(
            select(Designation).where(Designation.id == req.designation_id, Designation.organization_id == org_id)
        )
        if not des_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid designation ID")

    if req.shift_id:
        s_check = await db.execute(
            select(Shift).where(Shift.id == req.shift_id, Shift.organization_id == org_id)
        )
        if not s_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shift ID")

    person = Person(
        organization_id=org_id,
        unique_id=req.unique_id.strip(),
        full_name=req.full_name.strip(),
        email=req.email.lower() if req.email else None,
        phone=req.phone.strip() if req.phone else None,
        profile_photo_url=req.profile_photo_url,
        department_id=req.department_id,
        team_id=req.team_id,
        designation_id=req.designation_id,
        category=req.category or "employee",
        shift_id=req.shift_id,
        joining_date=req.joining_date,
        status=req.status or PersonStatus.ACTIVE,
        face_registered=FaceRegStatus.NOT_REGISTERED,
        custom_fields=req.custom_fields or {},
    )
    db.add(person)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_person",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Person",
        resource_id=str(person.id),
        details={"unique_id": person.unique_id, "name": person.full_name},
    )

    return PersonResponse.model_validate(person)


@router.get("/export")
async def export_people_csv(
    org_id: UUID,
    department_id: Optional[UUID] = Query(None),
    status: Optional[PersonStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = (
        select(Person)
        .options(selectinload(Person.department), selectinload(Person.team))
        .where(Person.organization_id == org_id)
    )
    if department_id:
        query = query.where(Person.department_id == department_id)
    if status:
        query = query.where(Person.status == status)

    result = await db.execute(query.order_by(Person.unique_id.asc()))
    people = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Unique ID",
        "Full Name",
        "Email",
        "Phone",
        "Department",
        "Team",
        "Category",
        "Status",
        "Face Registered",
        "Joining Date",
    ])

    for p in people:
        writer.writerow([
            p.unique_id,
            p.full_name,
            p.email or "",
            p.phone or "",
            p.department.name if p.department else "",
            p.team.name if p.team else "",
            p.category or "",
            p.status.value if hasattr(p.status, "value") else str(p.status),
            p.face_registered.value if hasattr(p.face_registered, "value") else str(p.face_registered),
            p.joining_date.isoformat() if p.joining_date else "",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="people_export_{org_id}.csv"'},
    )


@router.post("/import", response_model=PersonBulkImportResponse)
async def bulk_import_people_csv(
    org_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can import people")

    content = await file.read()
    try:
        decoded_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded_content = content.decode("latin-1")

    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    imported = 0
    failed = 0
    errors = []

    # Map existing departments by name
    dept_res = await db.execute(select(Department).where(Department.organization_id == org_id))
    dept_map = {d.name.lower(): d.id for d in dept_res.scalars().all()}

    # Map existing designations by name
    desig_res = await db.execute(select(Designation).where(Designation.organization_id == org_id))
    desig_map = {d.name.lower(): d.id for d in desig_res.scalars().all()}

    # Pre-fetch existing unique_ids
    existing_uids_res = await db.execute(select(Person.unique_id).where(Person.organization_id == org_id))
    existing_uids = set(existing_uids_res.scalars().all())

    row_num = 1
    for row in csv_reader:
        row_num += 1
        # Normalize headers
        norm_row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
        unique_id = norm_row.get("unique_id") or norm_row.get("id") or norm_row.get("code")
        full_name = norm_row.get("full_name") or norm_row.get("name")
        email = norm_row.get("email")
        phone = norm_row.get("phone")
        dept_name = norm_row.get("department")
        desig_name = norm_row.get("designation")
        category = norm_row.get("category", "employee")

        if not unique_id or not full_name:
            failed += 1
            errors.append(f"Row {row_num}: Missing unique_id or full_name")
            continue

        if unique_id in existing_uids:
            failed += 1
            errors.append(f"Row {row_num}: unique_id '{unique_id}' already exists")
            continue

        # Create or map department if provided
        dept_id = None
        if dept_name:
            dept_key = dept_name.lower()
            if dept_key in dept_map:
                dept_id = dept_map[dept_key]
            else:
                new_dept = Department(organization_id=org_id, name=dept_name)
                db.add(new_dept)
                await db.flush()
                dept_id = new_dept.id
                dept_map[dept_key] = dept_id

        # Create or map designation if provided
        desig_id = None
        if desig_name:
            desig_key = desig_name.lower()
            if desig_key in desig_map:
                desig_id = desig_map[desig_key]
            else:
                new_desig = Designation(organization_id=org_id, name=desig_name)
                db.add(new_desig)
                await db.flush()
                desig_id = new_desig.id
                desig_map[desig_key] = desig_id

        person = Person(
            organization_id=org_id,
            unique_id=unique_id,
            full_name=full_name,
            email=email.lower() if email else None,
            phone=phone if phone else None,
            department_id=dept_id,
            designation_id=desig_id,
            category=category or "employee",
            status=PersonStatus.ACTIVE,
            face_registered=FaceRegStatus.NOT_REGISTERED,
            custom_fields={},
        )
        db.add(person)
        existing_uids.add(unique_id)
        imported += 1

    await db.flush()
    await log_audit_event(
        db=db,
        action="bulk_import_people",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Person",
        details={"imported": imported, "failed": failed},
    )

    return PersonBulkImportResponse(imported=imported, failed=failed, errors=errors)


@router.post("/bulk", response_model=PersonBulkImportResponse)
async def bulk_import_people_json(
    org_id: UUID,
    payload: PersonBulkImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can import people")

    imported = 0
    failed = 0
    errors = []

    existing_uids_res = await db.execute(select(Person.unique_id).where(Person.organization_id == org_id))
    existing_uids = set(existing_uids_res.scalars().all())

    dept_res = await db.execute(select(Department).where(Department.organization_id == org_id))
    dept_map = {d.name.lower(): d.id for d in dept_res.scalars().all()}

    desig_res = await db.execute(select(Designation).where(Designation.organization_id == org_id))
    desig_map = {d.name.lower(): d.id for d in desig_res.scalars().all()}

    for idx, row in enumerate(payload.people, start=1):
        if not row.unique_id or not row.full_name:
            failed += 1
            errors.append(f"Item {idx}: Missing unique_id or full_name")
            continue

        if row.unique_id in existing_uids:
            failed += 1
            errors.append(f"Item {idx}: ID '{row.unique_id}' already exists")
            continue

        dept_id = None
        if row.department:
            k = row.department.lower()
            if k in dept_map:
                dept_id = dept_map[k]
            else:
                new_d = Department(organization_id=org_id, name=row.department)
                db.add(new_d)
                await db.flush()
                dept_id = new_d.id
                dept_map[k] = dept_id

        desig_id = None
        if row.designation:
            k = row.designation.lower()
            if k in desig_map:
                desig_id = desig_map[k]
            else:
                new_des = Designation(organization_id=org_id, name=row.designation)
                db.add(new_des)
                await db.flush()
                desig_id = new_des.id
                desig_map[k] = desig_id

        person = Person(
            organization_id=org_id,
            unique_id=row.unique_id,
            full_name=row.full_name,
            email=row.email.lower() if row.email else None,
            phone=row.phone if row.phone else None,
            department_id=dept_id,
            designation_id=desig_id,
            category=row.category or "employee",
            status=PersonStatus.ACTIVE,
            face_registered=FaceRegStatus.NOT_REGISTERED,
            custom_fields={},
        )
        db.add(person)
        existing_uids.add(row.unique_id)
        imported += 1

    await db.flush()
    return PersonBulkImportResponse(imported=imported, failed=failed, errors=errors)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    org_id: UUID,
    person_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(
        select(Person)
        .options(selectinload(Person.department), selectinload(Person.team))
        .where(Person.id == person_id, Person.organization_id == org_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    resp = PersonResponse.model_validate(person)
    if person.department:
        resp.department_name = person.department.name
    if person.team:
        resp.team_name = person.team.name
    if person.designation_id:
        desig = await db.scalar(select(Designation.name).where(Designation.id == person.designation_id))
        resp.designation_name = desig
    if person.shift_id:
        shift_name = await db.scalar(select(Shift.name).where(Shift.id == person.shift_id))
        resp.shift_name = shift_name

    return resp


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    org_id: UUID,
    person_id: UUID,
    req: PersonUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    if req.unique_id and req.unique_id.strip() != person.unique_id:
        existing = await db.execute(
            select(Person).where(
                Person.organization_id == org_id,
                Person.unique_id == req.unique_id.strip(),
                Person.id != person_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unique ID already taken")
        person.unique_id = req.unique_id.strip()

    update_dict = req.model_dump(exclude_unset=True, exclude={"unique_id"})
    for k, v in update_dict.items():
        if k == "email" and v:
            setattr(person, k, str(v).lower())
        else:
            setattr(person, k, v)

    person.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="update_person",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Person",
        resource_id=str(person_id),
        details={"name": person.full_name},
    )

    return await get_person(org_id=org_id, person_id=person_id, current_user=current_user, db=db)


@router.delete("/{person_id}", response_model=MessageResponse)
async def delete_person(
    org_id: UUID,
    person_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete people")

    result = await db.execute(
        select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    name = person.full_name
    await db.delete(person)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_person",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Person",
        resource_id=str(person_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Person '{name}' deleted successfully")


@router.get("/{person_id}/attendance", response_model=AttendanceRecordListResponse)
async def get_person_attendance_history(
    org_id: UUID,
    person_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    # Verify person belongs to org
    person_res = await db.execute(
        select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    )
    person = person_res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    query = select(AttendanceRecord).where(
        AttendanceRecord.organization_id == org_id,
        AttendanceRecord.person_id == person_id,
    )
    count_query = select(func.count(AttendanceRecord.id)).where(
        AttendanceRecord.organization_id == org_id,
        AttendanceRecord.person_id == person_id,
    )

    filters = []
    if start_date:
        filters.append(AttendanceRecord.date >= start_date)
    if end_date:
        filters.append(AttendanceRecord.date <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(AttendanceRecord.date.desc(), AttendanceRecord.created_at.desc()).offset(skip).limit(limit))
    records = result.scalars().all()

    items = []
    for r in records:
        resp = AttendanceRecordResponse.model_validate(r)
        resp.person_name = person.full_name
        resp.person_unique_id = person.unique_id
        items.append(resp)

    return AttendanceRecordListResponse(total=total, items=items)
