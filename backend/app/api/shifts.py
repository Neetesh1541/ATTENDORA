from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import Shift, Holiday, User, UserRole
from app.schemas.schemas import (
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    ShiftListResponse,
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse,
    HolidayListResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}", tags=["Shifts & Holidays"])


# ═══════════════════════════════════════════════════════════════════════════
# SHIFTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/shifts", response_model=ShiftListResponse)
async def list_shifts(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Shift).where(Shift.organization_id == org_id)
    count_query = select(func.count(Shift.id)).where(Shift.organization_id == org_id)

    if is_active is not None:
        query = query.where(Shift.is_active == is_active)
        count_query = count_query.where(Shift.is_active == is_active)

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Shift.created_at.asc()).offset(skip).limit(limit))
    shifts = result.scalars().all()

    return ShiftListResponse(
        total=total,
        items=[ShiftResponse.model_validate(s) for s in shifts],
    )


@router.post("/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    org_id: UUID,
    req: ShiftCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create shifts")

    existing = await db.execute(
        select(Shift).where(Shift.organization_id == org_id, Shift.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shift with this name already exists")

    shift = Shift(
        organization_id=org_id,
        name=req.name.strip(),
        start_time=req.start_time,
        end_time=req.end_time,
        grace_period_minutes=req.grace_period_minutes if req.grace_period_minutes is not None else 15,
        is_overnight=req.is_overnight if req.is_overnight is not None else False,
        is_active=req.is_active if req.is_active is not None else True,
    )
    db.add(shift)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_shift",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Shift",
        resource_id=str(shift.id),
        details={"name": shift.name, "start_time": shift.start_time, "end_time": shift.end_time},
    )

    return ShiftResponse.model_validate(shift)


@router.get("/shifts/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    org_id: UUID,
    shift_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.organization_id == org_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")

    return ShiftResponse.model_validate(shift)


@router.put("/shifts/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    org_id: UUID,
    shift_id: UUID,
    req: ShiftUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update shifts")

    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.organization_id == org_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")

    if req.name and req.name.strip() != shift.name:
        dup = await db.execute(
            select(Shift).where(Shift.organization_id == org_id, Shift.name == req.name.strip())
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shift name already in use")
        shift.name = req.name.strip()

    if req.start_time is not None:
        shift.start_time = req.start_time
    if req.end_time is not None:
        shift.end_time = req.end_time
    if req.grace_period_minutes is not None:
        shift.grace_period_minutes = req.grace_period_minutes
    if req.is_overnight is not None:
        shift.is_overnight = req.is_overnight
    if req.is_active is not None:
        shift.is_active = req.is_active

    await db.flush()

    await log_audit_event(
        db=db,
        action="update_shift",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Shift",
        resource_id=str(shift_id),
        details={"name": shift.name},
    )

    return ShiftResponse.model_validate(shift)


@router.delete("/shifts/{shift_id}", response_model=MessageResponse)
async def delete_shift(
    org_id: UUID,
    shift_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete shifts")

    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.organization_id == org_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")

    name = shift.name
    await db.delete(shift)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_shift",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Shift",
        resource_id=str(shift_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Shift '{name}' deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# HOLIDAYS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/holidays", response_model=HolidayListResponse)
async def list_holidays(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Holiday).where(Holiday.organization_id == org_id)
    count_query = select(func.count(Holiday.id)).where(Holiday.organization_id == org_id)

    if year:
        start_yr = date(year, 1, 1)
        end_yr = date(year, 12, 31)
        query = query.where(Holiday.date >= start_yr, Holiday.date <= end_yr)
        count_query = count_query.where(Holiday.date >= start_yr, Holiday.date <= end_yr)

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Holiday.date.asc()).offset(skip).limit(limit))
    holidays = result.scalars().all()

    return HolidayListResponse(
        total=total,
        items=[HolidayResponse.model_validate(h) for h in holidays],
    )


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    org_id: UUID,
    req: HolidayCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create holidays")

    existing = await db.execute(
        select(Holiday).where(Holiday.organization_id == org_id, Holiday.date == req.date)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Holiday already exists on this date")

    holiday = Holiday(
        organization_id=org_id,
        name=req.name.strip(),
        date=req.date,
        is_optional=req.is_optional if req.is_optional is not None else False,
    )
    db.add(holiday)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_holiday",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Holiday",
        resource_id=str(holiday.id),
        details={"name": holiday.name, "date": str(holiday.date)},
    )

    return HolidayResponse.model_validate(holiday)


@router.get("/holidays/{holiday_id}", response_model=HolidayResponse)
async def get_holiday(
    org_id: UUID,
    holiday_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id, Holiday.organization_id == org_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    return HolidayResponse.model_validate(holiday)


@router.put("/holidays/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    org_id: UUID,
    holiday_id: UUID,
    req: HolidayUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update holidays")

    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id, Holiday.organization_id == org_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    if req.date and req.date != holiday.date:
        dup = await db.execute(
            select(Holiday).where(Holiday.organization_id == org_id, Holiday.date == req.date)
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Holiday already exists on this date")
        holiday.date = req.date

    if req.name is not None:
        holiday.name = req.name.strip()
    if req.is_optional is not None:
        holiday.is_optional = req.is_optional

    await db.flush()

    await log_audit_event(
        db=db,
        action="update_holiday",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Holiday",
        resource_id=str(holiday_id),
        details={"name": holiday.name},
    )

    return HolidayResponse.model_validate(holiday)


@router.delete("/holidays/{holiday_id}", response_model=MessageResponse)
async def delete_holiday(
    org_id: UUID,
    holiday_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete holidays")

    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id, Holiday.organization_id == org_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    name = holiday.name
    await db.delete(holiday)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_holiday",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Holiday",
        resource_id=str(holiday_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Holiday '{name}' deleted successfully")
