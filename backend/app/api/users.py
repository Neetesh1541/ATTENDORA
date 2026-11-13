from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import hash_password
from app.core.dependencies import (
    get_current_active_user,
    verify_org_access,
)
from app.models.models import User, UserRole, Person, Organization, utcnow
from app.schemas.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(User).where(User.organization_id == org_id)
    count_query = select(func.count(User.id)).where(User.organization_id == org_id)

    filters = []
    if role is not None:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(User.full_name.ilike(search_pattern) | User.email.ilike(search_pattern))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(User.created_at.desc()).offset(skip).limit(limit))
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    org_id: UUID,
    req: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create users",
        )

    # Check email duplicate
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # If person_id provided, ensure person belongs to this org
    if req.person_id:
        person_res = await db.execute(
            select(Person).where(Person.id == req.person_id, Person.organization_id == org_id)
        )
        if not person_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced person does not belong to this organization",
            )

    new_user = User(
        organization_id=org_id,
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        phone=req.phone.strip() if req.phone else None,
        avatar_url=req.avatar_url,
        role=req.role or UserRole.MEMBER,
        is_active=req.is_active if req.is_active is not None else True,
        person_id=req.person_id,
    )
    db.add(new_user)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_user",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="User",
        resource_id=str(new_user.id),
        details={"created_email": new_user.email, "role": new_user.role.value},
    )

    return UserResponse.model_validate(new_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    org_id: UUID,
    user_id: UUID,
    req: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN) and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this user",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == org_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.email and req.email.lower() != target_user.email:
        existing = await db.execute(select(User).where(User.email == req.email.lower()))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already taken")
        target_user.email = req.email.lower()

    if req.full_name is not None:
        target_user.full_name = req.full_name.strip()
    if req.phone is not None:
        target_user.phone = req.phone.strip() if req.phone else None
    if req.avatar_url is not None:
        target_user.avatar_url = req.avatar_url
    if req.password is not None and req.password.strip():
        target_user.hashed_password = hash_password(req.password)

    # Only admins can change role or active status
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        if req.role is not None:
            target_user.role = req.role
        if req.is_active is not None:
            target_user.is_active = req.is_active
        if req.person_id is not None:
            target_user.person_id = req.person_id

    target_user.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="update_user",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="User",
        resource_id=str(user_id),
        details={"updated_user": target_user.email},
    )

    return UserResponse.model_validate(target_user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete users")

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == org_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    deleted_email = target_user.email
    await db.delete(target_user)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_user",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="User",
        resource_id=str(user_id),
        details={"deleted_email": deleted_email},
    )

    return MessageResponse(message=f"User {deleted_email} deleted successfully")
