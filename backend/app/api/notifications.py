from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.models import Notification, User
from app.schemas.schemas import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    MessageResponse,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    count_query = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read.is_(False))
        count_query = count_query.where(Notification.is_read.is_(False))

    total = await db.scalar(count_query) or 0
    result = await db.execute(
        query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    )
    notifications = result.scalars().all()

    return NotificationListResponse(
        total=total,
        items=[NotificationResponse.model_validate(n) for n in notifications],
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ) or 0

    return UnreadCountResponse(unread_count=count)


@router.patch("/read-all", response_model=MessageResponse)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.flush()

    return MessageResponse(message="All notifications marked as read")


@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == id, Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    await db.flush()

    return NotificationResponse.model_validate(notif)
