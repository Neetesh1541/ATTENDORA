from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import (
    get_current_active_user,
    verify_org_access,
    require_super_admin,
    require_org_admin,
)
from app.models.models import (
    Organization,
    OrgStatus,
    User,
    Person,
    PersonStatus,
    Department,
    Camera,
    Shift,
    AttendanceRecord,
    AttendanceStatus,
    UserRole,
    utcnow,
)
from app.schemas.schemas import (
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationStatusUpdate,
    OrganizationListResponse,
    OrganizationStatsResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[OrgStatus] = Query(None),
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    query = select(Organization)
    count_query = select(func.count(Organization.id))

    filters = []
    if status_filter:
        filters.append(Organization.status == status_filter)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(Organization.name.ilike(search_pattern) | Organization.slug.ilike(search_pattern))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Organization.created_at.desc()).offset(skip).limit(limit))
    orgs = result.scalars().all()

    return OrganizationListResponse(
        total=total,
        items=[OrganizationResponse.model_validate(o) for o in orgs],
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return OrganizationResponse.model_validate(org)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    req: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only org admins can update organization settings")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(org, field, val)

    org.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="update_organization",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Organization",
        resource_id=str(org_id),
        details={"updated_fields": list(update_data.keys())},
    )

    return OrganizationResponse.model_validate(org)


@router.patch("/{org_id}/status", response_model=OrganizationResponse)
async def update_organization_status(
    org_id: UUID,
    req: OrganizationStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can change organization status",
        )

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    org.status = req.status
    org.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="change_org_status",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Organization",
        resource_id=str(org_id),
        details={"new_status": req.status.value},
    )

    return OrganizationResponse.model_validate(org)


@router.get("/{org_id}/stats", response_model=OrganizationStatsResponse)
async def get_organization_stats(
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

    total_users = await db.scalar(
        select(func.count(User.id)).where(User.organization_id == org_id)
    ) or 0

    total_depts = await db.scalar(
        select(func.count(Department.id)).where(Department.organization_id == org_id)
    ) or 0

    total_cameras = await db.scalar(
        select(func.count(Camera.id)).where(
            Camera.organization_id == org_id,
            Camera.is_active.is_(True),
        )
    ) or 0

    total_shifts = await db.scalar(
        select(func.count(Shift.id)).where(
            Shift.organization_id == org_id,
            Shift.is_active.is_(True),
        )
    ) or 0

    # Today's attendance counts
    present_count = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]),
        )
    ) or 0

    late_count = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date == today,
            AttendanceRecord.is_late.is_(True),
        )
    ) or 0

    absent_count = max(0, total_people - present_count)

    rate = round((present_count / total_people * 100), 2) if total_people > 0 else 0.0

    return OrganizationStatsResponse(
        total_people=total_people,
        total_users=total_users,
        total_departments=total_depts,
        total_cameras=total_cameras,
        total_active_shifts=total_shifts,
        today_present=present_count,
        today_absent=absent_count,
        today_late=late_count,
        attendance_rate=rate,
    )
