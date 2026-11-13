from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


# ─── Face Registration Schemas ──────────────────────────────────────────────

class FaceRegisterBase64Request(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded face image (PNG/JPEG/WebP)")


class FaceVerifyRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64 encoded image to verify against registered face")


class FaceConsentRequest(BaseModel):
    consent_given: bool = Field(True, description="Whether explicit biometric consent is granted")
    ip_address: Optional[str] = Field(None, description="IP address of the user submitting consent")


class FaceProfileResponse(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    organization_id: uuid.UUID
    image_url: Optional[str] = None
    quality_score: Optional[float] = None
    registered_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FaceRegistrationResultResponse(BaseModel):
    success: bool
    message: str
    quality_score: Optional[float] = None
    face_profile: Optional[Dict[str, Any]] = None


class FaceStatusResponse(BaseModel):
    person_id: uuid.UUID
    organization_id: uuid.UUID
    face_registered: str
    registered_at: Optional[datetime] = None
    quality_score: Optional[float] = None
    image_url: Optional[str] = None
    has_consent: bool = False
    consent_date: Optional[datetime] = None


class FaceVerificationResponse(BaseModel):
    verified: bool
    person_id: uuid.UUID
    person_name: Optional[str] = None
    confidence: float
    distance: float
    threshold: float
    is_live: bool
    message: str


class FaceConsentResponse(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    organization_id: uuid.UUID
    consent_given: bool
    consent_date: datetime
    withdrawn: bool
    withdrawn_date: Optional[datetime] = None


# ─── Live Recognition Schemas ───────────────────────────────────────────────

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    top: int
    right: int
    bottom: int
    left: int


class SingleRecognitionResultSchema(BaseModel):
    person_id: Optional[str] = None
    name: Optional[str] = None
    unique_id: Optional[str] = None
    confidence: float
    distance: float
    bbox: BoundingBox
    is_recognized: bool
    status: str
    is_live: bool
    liveness_score: float
    liveness_details: Optional[Dict[str, Any]] = None


class FrameRecognitionRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded frame captured from video stream or camera")
    camera_id: Optional[uuid.UUID] = Field(None, description="UUID of the camera capturing the feed")
    session_id: Optional[uuid.UUID] = Field(None, description="Optional active attendance session ID")
    mark_attendance: bool = Field(False, description="Whether to automatically mark attendance upon recognition")
    action: Optional[str] = Field("check_in", description="Attendance action: check_in or check_out")


class FrameRecognitionResponse(BaseModel):
    faces_detected: int
    faces_recognized: int
    unknown_count: int
    results: List[SingleRecognitionResultSchema]
    recognized_people: List[Dict[str, Any]]
    newly_marked: List[Dict[str, Any]] = []
    processing_time_ms: float


class RecognitionLogItem(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    camera_id: Optional[uuid.UUID] = None
    camera_name: Optional[str] = None
    person_id: Optional[uuid.UUID] = None
    person_name: Optional[str] = None
    recognized: bool
    confidence: Optional[float] = None
    faces_detected: int
    faces_recognized: int
    timestamp: datetime

    class Config:
        from_attributes = True


class RecognitionLogsPaginationResponse(BaseModel):
    total: int
    page: int
    limit: int
    logs: List[RecognitionLogItem]
