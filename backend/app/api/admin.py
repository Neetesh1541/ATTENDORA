from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.models.models import (
    Organization,
    OrgStatus,
    User,
    Person,
    Camera,
    AttendanceRecord,
    SubscriptionPlanModel,
    OrganizationSubscription,
    SubscriptionStatus,
    AuditLog,
)
from app.schemas.schemas import (
    AdminStatsResponse,
    OrganizationListResponse,
    OrganizationResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanListResponse,
    AuditLogListResponse,
    AuditLogResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/admin", tags=["Super Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_platform_stats(
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    total_orgs = await db.scalar(select(func.count(Organization.id))) or 0
    active_orgs = await db.scalar(
        select(func.count(Organization.id)).where(Organization.status == OrgStatus.ACTIVE)
    ) or 0
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_people = await db.scalar(select(func.count(Person.id))) or 0
    today_att = await db.scalar(
        select(func.count(AttendanceRecord.id)).where(AttendanceRecord.date == today)
    ) or 0
    total_cams = await db.scalar(select(func.count(Camera.id))) or 0
    active_subs = await db.scalar(
        select(func.count(OrganizationSubscription.id)).where(
            OrganizationSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        )
    ) or 0

    return AdminStatsResponse(
        total_organizations=total_orgs,
        active_organizations=active_orgs,
        total_users=total_users,
        total_people=total_people,
        total_attendance_today=today_att,
        total_cameras=total_cams,
        active_subscriptions=active_subs,
    )


@router.get("/organizations", response_model=OrganizationListResponse)
async def get_all_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[OrgStatus] = Query(None),
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    query = select(Organization)
    count_query = select(func.count(Organization.id))

    filters = []
    if status is not None:
        filters.append(Organization.status == status)
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


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    organization_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    filters = []
    if organization_id:
        filters.append(AuditLog.organization_id == organization_id)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if action:
        filters.append(AuditLog.action.ilike(f"%{action.strip()}%"))
    if start_date:
        filters.append(func.date(AuditLog.timestamp) >= start_date)
    if end_date:
        filters.append(func.date(AuditLog.timestamp) <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit))
    logs = result.scalars().all()

    return AuditLogListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(l) for l in logs],
    )


@router.post("/plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    req: SubscriptionPlanCreate,
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(SubscriptionPlanModel).where(SubscriptionPlanModel.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan with this name already exists")

    plan = SubscriptionPlanModel(
        name=req.name.strip(),
        plan_type=req.plan_type,
        max_people=req.max_people,
        max_cameras=req.max_cameras,
        max_admins=req.max_admins,
        price_monthly=req.price_monthly,
        price_yearly=req.price_yearly,
        features=req.features or [],
        is_active=req.is_active if req.is_active is not None else True,
    )
    db.add(plan)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_subscription_plan",
        user_id=current_user.id,
        resource_type="SubscriptionPlan",
        resource_id=str(plan.id),
        details={"name": plan.name, "plan_type": plan.plan_type.value},
    )

    return SubscriptionPlanResponse.model_validate(plan)


@router.get("/plans", response_model=SubscriptionPlanListResponse)
async def list_subscription_plans(
    current_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SubscriptionPlanModel).order_by(SubscriptionPlanModel.price_monthly.asc()))
    plans = result.scalars().all()

    return SubscriptionPlanListResponse(
        total=len(plans),
        items=[SubscriptionPlanResponse.model_validate(p) for p in plans],
    )
