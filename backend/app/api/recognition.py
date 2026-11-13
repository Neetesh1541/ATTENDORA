import asyncio
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.detector import load_image_from_base64
from app.ai.pipeline import pipeline
from app.ai.recognizer import face_recognizer
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.models.models import (
    AttendanceAction,
    AttendanceRecord,
    AttendanceSession,
    AttendanceStatus,
    Camera,
    Person,
    RecognitionLog,
    Shift,
    utcnow,
)
from app.schemas.faces import (
    FrameRecognitionRequest,
    FrameRecognitionResponse,
    RecognitionLogItem,
    RecognitionLogsPaginationResponse,
    SingleRecognitionResultSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/organizations/{org_id}/recognition", tags=["Recognition"])
ws_router = APIRouter(tags=["Recognition WebSocket"])


async def _mark_person_attendance(
    person_id: uuid.UUID,
    org_id: uuid.UUID,
    camera_id: Optional[uuid.UUID],
    session_id: Optional[uuid.UUID],
    confidence: float,
    action_type: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """
    Helper function to mark attendance for a recognized individual in the database.
    Checks shift timings for late arrival calculation and suppresses duplicates.
    """
    today = utcnow().date()
    now_dt = utcnow()

    # Query Person with shift
    p_stmt = select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    p_res = await db.execute(p_stmt)
    person = p_res.scalar_one_or_none()
    if not person:
        return None

    # Check for existing attendance record today
    rec_stmt = select(AttendanceRecord).where(
        AttendanceRecord.organization_id == org_id,
        AttendanceRecord.person_id == person_id,
        AttendanceRecord.date == today,
    )
    if session_id:
        rec_stmt = rec_stmt.where(AttendanceRecord.session_id == session_id)

    rec_res = await db.execute(rec_stmt)
    existing_record = rec_res.scalar_one_or_none()

    # Case 1: Check-in
    if action_type == "check_in" or (action_type == "auto" and not existing_record):
        if existing_record:
            # Already checked in today
            return None

        # Check late status based on shift or org default
        is_late = False
        late_minutes = 0
        status_val = AttendanceStatus.PRESENT

        if person.shift_id:
            shift_stmt = select(Shift).where(Shift.id == person.shift_id)
            s_res = await db.execute(shift_stmt)
            shift = s_res.scalar_one_or_none()
            if shift and shift.start_time:
                try:
                    s_hour, s_min = map(int, shift.start_time.split(":"))
                    grace = shift.grace_period_minutes or 15
                    shift_dt = now_dt.replace(hour=s_hour, minute=s_min, second=0, microsecond=0)
                    if now_dt > shift_dt:
                        diff = int((now_dt - shift_dt).total_seconds() / 60)
                        if diff > grace:
                            is_late = True
                            late_minutes = diff
                            status_val = AttendanceStatus.LATE
                except Exception as e:
                    logger.debug(f"Shift calculation error: {e}")

        new_record = AttendanceRecord(
            organization_id=org_id,
            person_id=person_id,
            session_id=session_id,
            date=today,
            status=status_val,
            action=AttendanceAction.CHECK_IN,
            check_in_time=now_dt,
            is_late=is_late,
            late_minutes=late_minutes,
            camera_id=camera_id,
            recognition_confidence=round(confidence, 4),
            marked_by="ai",
            notes="Marked automatically via ATTENDORA Face Recognition",
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(new_record)
        await db.commit()

        return {
            "person_id": str(person.id),
            "name": person.full_name,
            "action": "check_in",
            "status": status_val.value,
            "time": now_dt.isoformat(),
            "confidence": confidence,
            "is_late": is_late,
        }

    # Case 2: Check-out
    elif action_type == "check_out" or (action_type == "auto" and existing_record):
        if not existing_record:
            # Cannot checkout without a checkin record
            return None

        # Update checkout time if not already marked or if updated
        existing_record.check_out_time = now_dt
        existing_record.action = AttendanceAction.CHECK_OUT

        if existing_record.check_in_time:
            hours = (now_dt - existing_record.check_in_time).total_seconds() / 3600.0
            existing_record.total_hours = round(max(0.0, hours), 2)

        existing_record.updated_at = now_dt
        await db.commit()

        return {
            "person_id": str(person.id),
            "name": person.full_name,
            "action": "check_out",
            "status": existing_record.status.value,
            "time": now_dt.isoformat(),
            "confidence": confidence,
            "total_hours": existing_record.total_hours,
        }

    return None


# ─── 1. Process Single Frame ─────────────────────────────────────────────────

@router.post("/frame", response_model=FrameRecognitionResponse)
async def process_frame_endpoint(
    org_id: uuid.UUID,
    payload: FrameRecognitionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Processes a single frame (base64 image) through the recognition pipeline:
    - Detects all faces
    - Checks passive liveness
    - Matches faces against organization members
    - Logs recognition event
    - Optionally marks attendance for recognized persons
    """
    try:
        frame_rgb = load_image_from_base64(payload.image_base64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode base64 frame: {str(e)}",
        )

    pipeline_result = await pipeline.process_frame(
        frame=frame_rgb,
        org_id=org_id,
        camera_id=payload.camera_id,
        db=db,
        is_bgr=False,
        log_to_db=True,
    )

    newly_marked: List[Dict[str, Any]] = []

    if payload.mark_attendance:
        action = payload.action or "check_in"
        cam_or_session = payload.session_id or payload.camera_id or org_id

        for person_data in pipeline_result.recognized_people:
            pid_str = person_data["person_id"]
            conf = person_data["confidence"]
            try:
                pid = uuid.UUID(pid_str)
            except ValueError:
                continue

            # Verify deduplication cooldown
            if face_recognizer.should_record_attendance(org_id, cam_or_session, pid, cooldown_seconds=60):
                marked = await _mark_person_attendance(
                    person_id=pid,
                    org_id=org_id,
                    camera_id=payload.camera_id,
                    session_id=payload.session_id,
                    confidence=conf,
                    action_type=action,
                    db=db,
                )
                if marked:
                    newly_marked.append(marked)

    return FrameRecognitionResponse(
        faces_detected=pipeline_result.faces_detected,
        faces_recognized=pipeline_result.faces_recognized,
        unknown_count=pipeline_result.unknown_count,
        results=[
            SingleRecognitionResultSchema(
                person_id=r.person_id,
                name=r.name,
                unique_id=r.unique_id,
                confidence=r.confidence,
                distance=r.distance,
                bbox=r.bbox,
                is_recognized=r.is_recognized,
                status=r.status,
                is_live=r.is_live,
                liveness_score=r.liveness_score,
                liveness_details=r.liveness_details,
            )
            for r in pipeline_result.results
        ],
        recognized_people=pipeline_result.recognized_people,
        newly_marked=newly_marked,
        processing_time_ms=pipeline_result.processing_time_ms,
    )


# ─── 2. Get Recognition Logs ─────────────────────────────────────────────────

@router.get("/logs", response_model=RecognitionLogsPaginationResponse)
async def get_recognition_logs_endpoint(
    org_id: uuid.UUID,
    camera_id: Optional[uuid.UUID] = Query(None, description="Filter by camera ID"),
    person_id: Optional[uuid.UUID] = Query(None, description="Filter by person ID"),
    recognized: Optional[bool] = Query(None, description="Filter by recognition status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated recognition logs for an organization with optional filters.
    """
    # Count query
    count_stmt = select(func.count(RecognitionLog.id)).where(RecognitionLog.organization_id == org_id)
    if camera_id:
        count_stmt = count_stmt.where(RecognitionLog.camera_id == camera_id)
    if person_id:
        count_stmt = count_stmt.where(RecognitionLog.person_id == person_id)
    if recognized is not None:
        count_stmt = count_stmt.where(RecognitionLog.recognized == recognized)

    total = (await db.execute(count_stmt)).scalar() or 0

    # Query rows with outer joins
    query = (
        select(RecognitionLog, Person.full_name, Camera.name)
        .outerjoin(Person, RecognitionLog.person_id == Person.id)
        .outerjoin(Camera, RecognitionLog.camera_id == Camera.id)
        .where(RecognitionLog.organization_id == org_id)
    )

    if camera_id:
        query = query.where(RecognitionLog.camera_id == camera_id)
    if person_id:
        query = query.where(RecognitionLog.person_id == person_id)
    if recognized is not None:
        query = query.where(RecognitionLog.recognized == recognized)

    offset = (page - 1) * limit
    query = query.order_by(RecognitionLog.timestamp.desc()).offset(offset).limit(limit)

    rows = (await db.execute(query)).all()

    logs = []
    for log, person_name, camera_name in rows:
        logs.append(
            RecognitionLogItem(
                id=log.id,
                organization_id=log.organization_id,
                camera_id=log.camera_id,
                camera_name=camera_name,
                person_id=log.person_id,
                person_name=person_name,
                recognized=log.recognized,
                confidence=log.confidence,
                faces_detected=log.faces_detected,
                faces_recognized=log.faces_recognized,
                timestamp=log.timestamp,
            )
        )

    return RecognitionLogsPaginationResponse(
        total=total,
        page=page,
        limit=limit,
        logs=logs,
    )


# ─── 3. Real-Time Recognition WebSocket Stream ───────────────────────────────

@ws_router.websocket("/ws/recognition/{org_id}/{camera_id}")
async def websocket_recognition_stream(
    websocket: WebSocket,
    org_id: uuid.UUID,
    camera_id: uuid.UUID,
):
    """
    Real-time bidirectional WebSocket stream for camera face recognition and attendance:
    1. Client streams base64 video frames:
       {"frame": "<base64>", "session_id": "<uuid or null>", "action": "check_in" | "check_out" | "auto"}
    2. Backend passes frame through RecognitionPipeline
    3. Live anti-spoofing and matching against organization database
    4. Automatically records attendance when an eligible person is recognized
    5. Streams back recognition bboxes, names, confidences, and newly marked attendance
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for org {org_id}, camera {camera_id}")

    # Camera status update to ONLINE
    async with AsyncSessionLocal() as db:
        c_stmt = select(Camera).where(Camera.id == camera_id, Camera.organization_id == org_id)
        cam = (await db.execute(c_stmt)).scalar_one_or_none()
        if cam:
            cam.last_active = utcnow()
            await db.commit()

    last_frame_time = time.perf_counter()
    fps = 0.0

    try:
        while True:
            # Receive frame data from client
            raw_data = await websocket.receive_text()
            now = time.perf_counter()
            delta = now - last_frame_time
            if delta > 0:
                fps = round(1.0 / delta, 1)
            last_frame_time = now

            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Malformed JSON payload"})
                continue

            # Heartbeat ping/pong
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": utcnow().isoformat()})
                continue

            frame_b64 = msg.get("frame")
            if not frame_b64:
                await websocket.send_json({"error": "Missing 'frame' in message"})
                continue

            session_id_str = msg.get("session_id")
            session_id = uuid.UUID(session_id_str) if session_id_str else None
            action_type = msg.get("action", "auto")

            # Decode frame
            try:
                frame_rgb = load_image_from_base64(frame_b64)
            except Exception as e:
                await websocket.send_json({"error": f"Frame decoding error: {str(e)}"})
                continue

            async with AsyncSessionLocal() as db:
                pipeline_result = await pipeline.process_frame(
                    frame=frame_rgb,
                    org_id=org_id,
                    camera_id=camera_id,
                    db=db,
                    is_bgr=False,
                    log_to_db=True,
                )

                newly_marked: List[Dict[str, Any]] = []
                cam_or_session = session_id or camera_id

                # Attendance marking loop
                for person_data in pipeline_result.recognized_people:
                    pid_str = person_data["person_id"]
                    conf = person_data["confidence"]
                    try:
                        pid = uuid.UUID(pid_str)
                    except ValueError:
                        continue

                    if conf >= settings.MIN_FACE_CONFIDENCE:
                        # Deduplication cooldown check (e.g. 60s)
                        if face_recognizer.should_record_attendance(
                            org_id=org_id,
                            session_or_camera_id=cam_or_session,
                            person_id=pid,
                            cooldown_seconds=60,
                        ):
                            marked = await _mark_person_attendance(
                                person_id=pid,
                                org_id=org_id,
                                camera_id=camera_id,
                                session_id=session_id,
                                confidence=conf,
                                action_type=action_type,
                                db=db,
                            )
                            if marked:
                                newly_marked.append(marked)

                # Send response back to WebSocket client
                response_payload = {
                    "faces_detected": pipeline_result.faces_detected,
                    "recognized": pipeline_result.recognized_people,
                    "unknown_count": pipeline_result.unknown_count,
                    "results": [r.to_dict() for r in pipeline_result.results],
                    "newly_marked": newly_marked,
                    "fps": fps,
                    "processing_time_ms": pipeline_result.processing_time_ms,
                }
                await websocket.send_json(response_payload)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error in camera {camera_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
