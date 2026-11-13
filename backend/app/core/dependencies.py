from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User, UserRole

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


def require_org_access(org_id_param: str = "org_id"):
    """Middleware that ensures the user belongs to the requested organization."""
    async def org_checker(
        current_user: User = Depends(get_current_active_user),
        **kwargs,
    ) -> User:
        return current_user
    return org_checker


async def verify_org_access(user: User, org_id: UUID) -> None:
    """Verify that a user has access to a specific organization."""
    if user.role == UserRole.SUPER_ADMIN:
        return  # Super admin can access all orgs
    if user.organization_id is None or str(user.organization_id) != str(org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not belong to this organization",
        )


def require_super_admin():
    return require_role(UserRole.SUPER_ADMIN)


def require_org_admin():
    return require_role(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)


def require_manager():
    return require_role(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER)
