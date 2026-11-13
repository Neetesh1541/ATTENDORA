from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import Camera, CameraStatus, User, UserRole, utcnow
from app.schemas.schemas import (
    CameraCreate,
    CameraUpdate,
    CameraStatusUpdate,
    CameraResponse,
    CameraListResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}/cameras", tags=["Cameras"])


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[CameraStatus] = Query(None),
    camera_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Camera).where(Camera.organization_id == org_id)
    count_query = select(func.count(Camera.id)).where(Camera.organization_id == org_id)

    filters = []
    if status is not None:
        filters.append(Camera.status == status)
    if camera_type is not None:
        filters.append(Camera.camera_type == camera_type)
    if is_active is not None:
        filters.append(Camera.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(Camera.name.ilike(search_pattern) | Camera.location.ilike(search_pattern))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Camera.name.asc()).offset(skip).limit(limit))
    cameras = result.scalars().all()

    return CameraListResponse(
        total=total,
        items=[CameraResponse.model_validate(c) for c in cameras],
    )


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def add_camera(
    org_id: UUID,
    req: CameraCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can add cameras")

    existing = await db.execute(
        select(Camera).where(Camera.organization_id == org_id, Camera.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera with this name already exists")

    camera = Camera(
        organization_id=org_id,
        name=req.name.strip(),
        location=req.location,
        camera_type=req.camera_type or "webcam",
        stream_url=req.stream_url,
        status=CameraStatus.OFFLINE,
        is_active=req.is_active if req.is_active is not None else True,
        settings=req.settings or {},
    )
    db.add(camera)
    await db.flush()

    await log_audit_event(
        db=db,
        action="add_camera",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Camera",
        resource_id=str(camera.id),
        details={"name": camera.name, "location": camera.location},
    )

    return CameraResponse.model_validate(camera)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    org_id: UUID,
    camera_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id, Camera.organization_id == org_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    return CameraResponse.model_validate(camera)


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    org_id: UUID,
    camera_id: UUID,
    req: CameraUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update cameras")

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id, Camera.organization_id == org_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    if req.name and req.name.strip() != camera.name:
        dup = await db.execute(
            select(Camera).where(Camera.organization_id == org_id, Camera.name == req.name.strip())
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera name already in use")
        camera.name = req.name.strip()

    if req.location is not None:
        camera.location = req.location
    if req.camera_type is not None:
        camera.camera_type = req.camera_type
    if req.stream_url is not None:
        camera.stream_url = req.stream_url
    if req.status is not None:
        camera.status = req.status
    if req.is_active is not None:
        camera.is_active = req.is_active
    if req.settings is not None:
        camera.settings = req.settings

    camera.updated_at = utcnow()
    await db.flush()

    await log_audit_event(
        db=db,
        action="update_camera",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Camera",
        resource_id=str(camera_id),
        details={"name": camera.name},
    )

    return CameraResponse.model_validate(camera)


@router.delete("/{camera_id}", response_model=MessageResponse)
async def delete_camera(
    org_id: UUID,
    camera_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete cameras")

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id, Camera.organization_id == org_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    name = camera.name
    await db.delete(camera)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_camera",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Camera",
        resource_id=str(camera_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Camera '{name}' deleted successfully")


@router.patch("/{camera_id}/status", response_model=CameraResponse)
async def update_camera_status(
    org_id: UUID,
    camera_id: UUID,
    req: CameraStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id, Camera.organization_id == org_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    camera.status = req.status
    if req.status == CameraStatus.ONLINE:
        camera.last_active = utcnow()
    camera.updated_at = utcnow()
    await db.flush()

    return CameraResponse.model_validate(camera)
