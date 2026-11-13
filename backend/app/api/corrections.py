from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    AttendanceCorrection,
    AttendanceRecord,
    CorrectionStatus,
    Notification,
    NotificationType,
    User,
    UserRole,
    Person,
    utcnow,
)
from app.schemas.schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceCorrectionResponse,
    AttendanceCorrectionListResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}/corrections", tags=["Attendance Corrections"])


@router.post("", response_model=AttendanceCorrectionResponse, status_code=status.HTTP_201_CREATED)
async def request_correction(
    org_id: UUID,
    req: AttendanceCorrectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    # Verify attendance record exists in this org
    rec_res = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.id == req.attendance_record_id,
            AttendanceRecord.organization_id == org_id,
        )
    )
    record = rec_res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

    correction = AttendanceCorrection(
        organization_id=org_id,
        attendance_record_id=record.id,
        requested_by=current_user.id,
        original_status=record.status,
        requested_status=req.requested_status,
        original_check_in=record.check_in_time,
        requested_check_in=req.requested_check_in,
        original_check_out=record.check_out_time,
        requested_check_out=req.requested_check_out,
        reason=req.reason.strip(),
        status=CorrectionStatus.PENDING,
    )
    db.add(correction)
    await db.flush()

    # Create notification for organization admins
    admins_res = await db.execute(
        select(User).where(
            User.organization_id == org_id,
            User.role.in_([UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]),
        )
    )
    admins = admins_res.scalars().all()
    for adm in admins:
        notif = Notification(
            organization_id=org_id,
            user_id=adm.id,
            type=NotificationType.CORRECTION_REQUEST,
            title="Attendance Correction Request",
            message=f"{current_user.full_name} requested a correction for attendance record on {record.date}.",
            data={"correction_id": str(correction.id), "record_id": str(record.id)},
        )
        db.add(notif)

    await log_audit_event(
        db=db,
        action="request_attendance_correction",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="AttendanceCorrection",
        resource_id=str(correction.id),
        details={"record_id": str(record.id), "reason": correction.reason},
    )

    resp = AttendanceCorrectionResponse.model_validate(correction)
    resp.requester_name = current_user.full_name
    return resp


@router.get("", response_model=AttendanceCorrectionListResponse)
async def list_corrections(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[CorrectionStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = (
        select(AttendanceCorrection, User.full_name.label("requester_name"), Person.full_name.label("person_name"))
        .join(User, AttendanceCorrection.requested_by == User.id)
        .join(AttendanceRecord, AttendanceCorrection.attendance_record_id == AttendanceRecord.id)
        .join(Person, AttendanceRecord.person_id == Person.id)
        .where(AttendanceCorrection.organization_id == org_id)
    )
    count_query = (
        select(func.count(AttendanceCorrection.id))
        .where(AttendanceCorrection.organization_id == org_id)
    )

    if status:
        query = query.where(AttendanceCorrection.status == status)
        count_query = count_query.where(AttendanceCorrection.status == status)

    total = await db.scalar(count_query) or 0
    result = await db.execute(
        query.order_by(AttendanceCorrection.created_at.desc()).offset(skip).limit(limit)
    )
    rows = result.all()

    items = []
    for corr, req_name, pers_name in rows:
        resp = AttendanceCorrectionResponse.model_validate(corr)
        resp.requester_name = req_name
        resp.person_name = pers_name
        items.append(resp)

    return AttendanceCorrectionListResponse(total=total, items=items)


@router.patch("/{id}/approve", response_model=AttendanceCorrectionResponse)
async def approve_correction(
    org_id: UUID,
    id: UUID,
    review_req: Optional[AttendanceCorrectionReview] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    res = await db.execute(
        select(AttendanceCorrection).where(
            AttendanceCorrection.id == id,
            AttendanceCorrection.organization_id == org_id,
        )
    )
    corr = res.scalar_one_or_none()
    if not corr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correction request not found")

    if corr.status != CorrectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Correction request is already {corr.status.value}",
        )

    # Fetch underlying attendance record
    rec_res = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.id == corr.attendance_record_id)
    )
    record = rec_res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

    # Apply correction to attendance record
    record.status = corr.requested_status
    if corr.requested_check_in is not None:
        record.check_in_time = corr.requested_check_in
    if corr.requested_check_out is not None:
        record.check_out_time = corr.requested_check_out

    if record.check_in_time and record.check_out_time:
        diff_s = (record.check_out_time - record.check_in_time).total_seconds()
        record.total_hours = round(max(0.0, diff_s / 3600.0), 2)

    record.updated_at = utcnow()

    # Mark correction approved
    corr.status = CorrectionStatus.APPROVED
    corr.reviewed_by = current_user.id
    corr.reviewed_at = utcnow()
    if review_req and review_req.review_notes:
        corr.review_notes = review_req.review_notes

    # Send notification to requester
    notif = Notification(
        organization_id=org_id,
        user_id=corr.requested_by,
        type=NotificationType.CORRECTION_APPROVED,
        title="Attendance Correction Approved",
        message=f"Your attendance correction request for {record.date} was approved.",
        data={"correction_id": str(corr.id), "record_id": str(record.id)},
    )
    db.add(notif)
    await db.flush()

    await log_audit_event(
        db=db,
        action="approve_correction",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="AttendanceCorrection",
        resource_id=str(corr.id),
        details={"record_id": str(record.id)},
    )

    return AttendanceCorrectionResponse.model_validate(corr)


@router.patch("/{id}/reject", response_model=AttendanceCorrectionResponse)
async def reject_correction(
    org_id: UUID,
    id: UUID,
    review_req: Optional[AttendanceCorrectionReview] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    res = await db.execute(
        select(AttendanceCorrection).where(
            AttendanceCorrection.id == id,
            AttendanceCorrection.organization_id == org_id,
        )
    )
    corr = res.scalar_one_or_none()
    if not corr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correction request not found")

    if corr.status != CorrectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Correction request is already {corr.status.value}",
        )

    corr.status = CorrectionStatus.REJECTED
    corr.reviewed_by = current_user.id
    corr.reviewed_at = utcnow()
    if review_req and review_req.review_notes:
        corr.review_notes = review_req.review_notes

    # Send notification to requester
    notif = Notification(
        organization_id=org_id,
        user_id=corr.requested_by,
        type=NotificationType.CORRECTION_REJECTED,
        title="Attendance Correction Rejected",
        message=f"Your attendance correction request was rejected: {corr.review_notes or 'No reason provided'}",
        data={"correction_id": str(corr.id)},
    )
    db.add(notif)
    await db.flush()

    await log_audit_event(
        db=db,
        action="reject_correction",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="AttendanceCorrection",
        resource_id=str(corr.id),
        details={"review_notes": corr.review_notes},
    )

    return AttendanceCorrectionResponse.model_validate(corr)
