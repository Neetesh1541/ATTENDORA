import re
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.core.dependencies import get_current_active_user
from app.models.models import (
    User,
    UserRole,
    Organization,
    OrgStatus,
    Shift,
    OrganizationSubscription,
    SubscriptionPlanModel,
    SubscriptionPlan,
    SubscriptionStatus,
    utcnow,
)
from app.schemas.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ChangePasswordRequest,
    ProfileUpdateRequest,
    UserResponse,
    OrganizationResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def generate_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or "org"


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your administrator.",
        )

    # Check org status if user belongs to an org
    org = None
    if user.organization_id:
        org_result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
        org = org_result.scalar_one_or_none()
        if org and org.status == OrgStatus.DEACTIVATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization account is deactivated.",
            )

    user.last_login = utcnow()
    await db.flush()

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "org_id": str(user.organization_id) if user.organization_id else None,
    }
    access_token = create_access_token(data=token_payload)

    client_ip = request.client.host if request.client else None
    await log_audit_event(
        db=db,
        action="user_login",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="User",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=client_ip,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org) if org else None,
    )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Check if admin email already exists
    user_result = await db.execute(select(User).where(User.email == req.admin_email.lower()))
    if user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    # Generate a unique slug
    base_slug = req.org_slug.strip().lower() if req.org_slug else generate_slug(req.org_name)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(Organization).where(Organization.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create Organization
    org = Organization(
        name=req.org_name.strip(),
        slug=slug,
        org_type=req.org_type,
        timezone=req.timezone,
        status=OrgStatus.ACTIVE,
        working_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
        working_hours_start="09:00",
        working_hours_end="17:00",
        settings={},
    )
    db.add(org)
    await db.flush()

    # Create Admin User
    admin_user = User(
        organization_id=org.id,
        email=req.admin_email.lower(),
        hashed_password=hash_password(req.admin_password),
        full_name=req.admin_name.strip(),
        phone=req.phone,
        role=UserRole.ORG_ADMIN,
        is_active=True,
        last_login=utcnow(),
    )
    db.add(admin_user)
    await db.flush()

    # Create Default Shift
    default_shift = Shift(
        organization_id=org.id,
        name="General Shift",
        start_time="09:00",
        end_time="17:00",
        grace_period_minutes=15,
        is_overnight=False,
        is_active=True,
    )
    db.add(default_shift)

    # Attach Trial Subscription
    plan_result = await db.execute(
        select(SubscriptionPlanModel).where(SubscriptionPlanModel.plan_type == SubscriptionPlan.STARTER)
    )
    starter_plan = plan_result.scalar_one_or_none()

    today = date.today()
    subscription = OrganizationSubscription(
        organization_id=org.id,
        plan_id=starter_plan.id if starter_plan else None,
        status=SubscriptionStatus.TRIAL,
        start_date=today,
        end_date=today + timedelta(days=30),
    )
    db.add(subscription)
    await db.flush()

    token_payload = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role.value if hasattr(admin_user.role, "value") else str(admin_user.role),
        "org_id": str(org.id),
    }
    access_token = create_access_token(data=token_payload)

    client_ip = request.client.host if request.client else None
    await log_audit_event(
        db=db,
        action="organization_registered",
        organization_id=org.id,
        user_id=admin_user.id,
        resource_type="Organization",
        resource_id=str(org.id),
        details={"org_name": org.name, "admin_email": admin_user.email},
        ip_address=client_ip,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(admin_user),
        organization=OrganizationResponse.model_validate(org),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip() if req.phone else None
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url

    current_user.updated_at = utcnow()
    await db.flush()

    return UserResponse.model_validate(current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(req.new_password)
    current_user.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="password_changed",
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        resource_type="User",
        resource_id=str(current_user.id),
        details={"user_email": current_user.email},
    )

    return MessageResponse(message="Password updated successfully")
