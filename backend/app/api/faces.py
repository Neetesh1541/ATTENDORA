import base64
import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anti_spoof import detect_liveness
from app.ai.detector import (
    detect_faces,
    load_image_from_base64,
    load_image_from_bytes,
)
from app.ai.embeddings import (
    compare_embeddings,
    deserialize_embedding,
    distance_to_confidence,
    generate_embedding,
)
from app.ai.pipeline import pipeline
from app.core.config import settings
from app.core.database import get_db
from app.models.models import (
    FaceProfile,
    FaceRegStatus,
    FaceRegistrationConsent,
    Person,
    utcnow,
)
from app.schemas.faces import (
    FaceConsentRequest,
    FaceConsentResponse,
    FaceRegisterBase64Request,
    FaceRegistrationResultResponse,
    FaceStatusResponse,
    FaceVerificationResponse,
    FaceVerifyRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/organizations/{org_id}/faces", tags=["Face Registration"])


def _extract_image_bytes(
    file: Optional[UploadFile],
    base64_str: Optional[str],
) -> bytes:
    """Helper to extract raw image bytes from either UploadFile or base64 string."""
    if file is not None and file.filename:
        content = file.file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB",
            )
        return content

    if base64_str and isinstance(base64_str, str):
        raw_b64 = base64_str
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        try:
            content = base64.b64decode(raw_b64)
            if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image data exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB",
                )
            return content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 encoded image: {str(e)}",
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Please provide an image via file upload or base64 string.",
    )


# ─── 1. Register Face ────────────────────────────────────────────────────────

@router.post("/register/{person_id}", response_model=FaceRegistrationResultResponse)
@router.post("/{person_id}/register", response_model=FaceRegistrationResultResponse, include_in_schema=False)
async def register_face_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a face for a person in an organization.
    Accepts either a multipart file upload or form-encoded `image_base64`.
    """
    image_bytes = _extract_image_bytes(file, image_base64)

    success, message, quality_score, profile_dict = await pipeline.register_face(
        image_bytes=image_bytes,
        person_id=person_id,
        org_id=org_id,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return FaceRegistrationResultResponse(
        success=True,
        message=message,
        quality_score=quality_score,
        face_profile=profile_dict,
    )


@router.post("/register/{person_id}/json", response_model=FaceRegistrationResultResponse)
async def register_face_json_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    payload: FaceRegisterBase64Request,
    db: AsyncSession = Depends(get_db),
):
    """JSON-body endpoint to register a face using base64 encoded image."""
    image_bytes = _extract_image_bytes(None, payload.image_base64)

    success, message, quality_score, profile_dict = await pipeline.register_face(
        image_bytes=image_bytes,
        person_id=person_id,
        org_id=org_id,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return FaceRegistrationResultResponse(
        success=True,
        message=message,
        quality_score=quality_score,
        face_profile=profile_dict,
    )


# ─── 2. Update Face ──────────────────────────────────────────────────────────

@router.put("/update/{person_id}", response_model=FaceRegistrationResultResponse)
@router.put("/{person_id}/update", response_model=FaceRegistrationResultResponse, include_in_schema=False)
@router.put("/{person_id}", response_model=FaceRegistrationResultResponse, include_in_schema=False)
async def update_face_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Updates an existing face profile for a person."""
    image_bytes = _extract_image_bytes(file, image_base64)

    success, message, quality_score, profile_dict = await pipeline.update_face(
        image_bytes=image_bytes,
        person_id=person_id,
        org_id=org_id,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return FaceRegistrationResultResponse(
        success=True,
        message=message,
        quality_score=quality_score,
        face_profile=profile_dict,
    )


# ─── 3. Delete Face ──────────────────────────────────────────────────────────

@router.delete("/{person_id}")
async def delete_face_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Deletes face profile and resets person's face_registered status."""
    success, message = await pipeline.delete_face(
        person_id=person_id,
        org_id=org_id,
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    return {"success": True, "message": message}


# ─── 4. Get Status ───────────────────────────────────────────────────────────

@router.get("/{person_id}/status", response_model=FaceStatusResponse)
async def get_face_status_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Gets face registration status, profile photo url, quality score, and consent info."""
    stmt = select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    res = await db.execute(stmt)
    person = res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    # Fetch face profile
    profile_stmt = select(FaceProfile).where(
        FaceProfile.person_id == person_id,
        FaceProfile.organization_id == org_id,
    )
    p_res = await db.execute(profile_stmt)
    profile = p_res.scalar_one_or_none()

    # Fetch consent
    consent_stmt = select(FaceRegistrationConsent).where(
        FaceRegistrationConsent.person_id == person_id,
        FaceRegistrationConsent.organization_id == org_id,
    ).order_by(FaceRegistrationConsent.consent_date.desc())
    c_res = await db.execute(consent_stmt)
    consent = c_res.scalars().first()

    has_consent = (consent is not None and consent.consent_given and not consent.withdrawn)

    return FaceStatusResponse(
        person_id=person.id,
        organization_id=person.organization_id,
        face_registered=person.face_registered.value if hasattr(person.face_registered, "value") else str(person.face_registered),
        registered_at=profile.registered_at if profile else None,
        quality_score=profile.quality_score if profile else None,
        image_url=profile.image_url if profile else person.profile_photo_url,
        has_consent=has_consent,
        consent_date=consent.consent_date if consent else None,
    )


# ─── 5. Verify Face ──────────────────────────────────────────────────────────

@router.post("/verify/{person_id}", response_model=FaceVerificationResponse)
@router.post("/{person_id}/verify", response_model=FaceVerificationResponse, include_in_schema=False)
async def verify_face_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies that a provided face image matches the registered profile of a specific person (1:1 matching).
    """
    image_bytes = _extract_image_bytes(file, image_base64)

    # 1. Fetch registered profile
    profile_stmt = select(FaceProfile, Person).join(Person, FaceProfile.person_id == Person.id).where(
        FaceProfile.person_id == person_id,
        FaceProfile.organization_id == org_id,
    )
    result = await db.execute(profile_stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person does not have an active registered face profile.",
        )
    face_profile, person = row

    # 2. Decode probe image
    try:
        probe_image = load_image_from_bytes(image_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode verification image: {e}",
        )

    # 3. Detect face in probe image
    faces = detect_faces(probe_image, upsample=1)
    if not faces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the verification image.",
        )

    face_loc = faces[0]

    # 4. Anti-spoofing check
    is_live, liveness_score, _ = detect_liveness(probe_image, face_loc, is_bgr=False)

    # 5. Extract probe embedding
    probe_emb = generate_embedding(probe_image, face_location=face_loc)
    if probe_emb is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to compute facial embedding for verification.",
        )

    # 6. Compare with registered embedding
    registered_emb = deserialize_embedding(face_profile.encoding)
    distance = compare_embeddings(probe_emb, registered_emb)
    tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.45)
    confidence = distance_to_confidence(distance, tolerance)
    is_match = (distance <= tolerance)

    if not is_live:
        message = "Verification failed: anti-spoofing check detected possible spoofing."
        verified = False
    elif is_match:
        message = "Face verification successful. Match confirmed."
        verified = True
    else:
        message = "Verification failed: face does not match the registered profile."
        verified = False

    return FaceVerificationResponse(
        verified=verified,
        person_id=person.id,
        person_name=person.full_name,
        confidence=confidence,
        distance=round(distance, 4),
        threshold=tolerance,
        is_live=is_live,
        message=message,
    )


# ─── 6. Consent Management ───────────────────────────────────────────────────

@router.post("/consent/{person_id}", response_model=FaceConsentResponse)
@router.post("/{person_id}/consent", response_model=FaceConsentResponse, include_in_schema=False)
async def record_face_consent_endpoint(
    org_id: uuid.UUID,
    person_id: uuid.UUID,
    payload: FaceConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Records or updates biometric consent for face recognition in compliance with data privacy policies.
    """
    # Check person exists
    p_stmt = select(Person).where(Person.id == person_id, Person.organization_id == org_id)
    p_res = await db.execute(p_stmt)
    person = p_res.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    client_ip = payload.ip_address or request.client.host if request.client else None

    # Check existing consent record
    stmt = select(FaceRegistrationConsent).where(
        FaceRegistrationConsent.person_id == person_id,
        FaceRegistrationConsent.organization_id == org_id,
    )
    res = await db.execute(stmt)
    consent = res.scalar_one_or_none()

    if consent:
        consent.consent_given = payload.consent_given
        consent.consent_date = utcnow()
        consent.ip_address = client_ip
        consent.withdrawn = not payload.consent_given
        consent.withdrawn_date = utcnow() if not payload.consent_given else None
    else:
        consent = FaceRegistrationConsent(
            person_id=person_id,
            organization_id=org_id,
            consent_given=payload.consent_given,
            consent_date=utcnow(),
            ip_address=client_ip,
            withdrawn=not payload.consent_given,
            withdrawn_date=utcnow() if not payload.consent_given else None,
        )
        db.add(consent)

    await db.commit()
    await db.refresh(consent)

    return FaceConsentResponse(
        id=consent.id,
        person_id=consent.person_id,
        organization_id=consent.organization_id,
        consent_given=consent.consent_given,
        consent_date=consent.consent_date,
        withdrawn=consent.withdrawn,
        withdrawn_date=consent.withdrawn_date,
    )
