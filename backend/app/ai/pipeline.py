import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import numpy as np
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anti_spoof import detect_liveness
from app.ai.detector import (
    detect_faces,
    load_image_from_bytes,
    validate_image_quality,
)
from app.ai.embeddings import (
    generate_embedding,
    serialize_embedding,
)
from app.ai.recognizer import FaceRecognizer, RecognitionResult, face_recognizer
from app.core.config import settings
from app.models.models import (
    Camera,
    FaceProfile,
    FaceRegStatus,
    Person,
    PersonStatus,
    RecognitionLog,
    utcnow,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    faces_detected: int
    faces_recognized: int
    unknown_count: int
    results: List[RecognitionResult]
    recognized_people: List[Dict[str, Any]]
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faces_detected": self.faces_detected,
            "faces_recognized": self.faces_recognized,
            "unknown_count": self.unknown_count,
            "results": [r.to_dict() for r in self.results],
            "recognized_people": self.recognized_people,
            "processing_time_ms": self.processing_time_ms,
        }


class RecognitionPipeline:
    """
    High-level facial recognition pipeline orchestrator for ATTENDORA.
    Coordinates face detection, passive anti-spoofing, identity matching,
    database persistence of profiles, and audit logging.
    """

    def __init__(self, recognizer: Optional[FaceRecognizer] = None):
        self.recognizer = recognizer or face_recognizer
        self.faces_dir = os.path.join(settings.UPLOAD_DIR, "faces")
        os.makedirs(self.faces_dir, exist_ok=True)

    async def process_frame(
        self,
        frame: np.ndarray,
        org_id: Union[uuid.UUID, str],
        camera_id: Optional[Union[uuid.UUID, str]] = None,
        db: Optional[AsyncSession] = None,
        is_bgr: bool = True,
        log_to_db: bool = True,
    ) -> PipelineResult:
        """
        Processes a single video frame or still image through the complete recognition pipeline:
        1. Detects all faces in frame.
        2. Verifies passive liveness for each face.
        3. Matches facial embeddings against organization's registered database.
        4. Writes recognition event to RecognitionLog.
        5. Returns structured PipelineResult with UI coordinates and recognition statuses.
        """
        start_time = time.perf_counter()
        org_uuid = uuid.UUID(str(org_id)) if isinstance(org_id, str) else org_id
        cam_uuid = uuid.UUID(str(camera_id)) if camera_id else None

        results = await self.recognizer.recognize_frame(
            frame=frame,
            org_id=org_uuid,
            db=db,
            check_liveness=True,
            is_bgr=is_bgr,
        )

        faces_detected = len(results)
        faces_recognized = sum(1 for r in results if r.is_recognized)
        unknown_count = sum(1 for r in results if not r.is_recognized)

        recognized_people = []
        best_person_id = None
        max_confidence = 0.0

        for r in results:
            if r.is_recognized and r.person_id:
                recognized_people.append({
                    "person_id": r.person_id,
                    "name": r.name,
                    "unique_id": r.unique_id,
                    "confidence": r.confidence,
                    "bbox": r.bbox,
                    "status": r.status,
                })
                if r.confidence > max_confidence:
                    max_confidence = r.confidence
                    try:
                        best_person_id = uuid.UUID(r.person_id)
                    except ValueError:
                        best_person_id = None

        # Log recognition event to database if session is provided and faces were detected
        if log_to_db and db is not None:
            try:
                rec_log = RecognitionLog(
                    organization_id=org_uuid,
                    camera_id=cam_uuid,
                    person_id=best_person_id,
                    recognized=(faces_recognized > 0),
                    confidence=max_confidence if faces_recognized > 0 else 0.0,
                    faces_detected=faces_detected,
                    faces_recognized=faces_recognized,
                    timestamp=utcnow(),
                )
                db.add(rec_log)
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to record RecognitionLog: {e}")
                await db.rollback()

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return PipelineResult(
            faces_detected=faces_detected,
            faces_recognized=faces_recognized,
            unknown_count=unknown_count,
            results=results,
            recognized_people=recognized_people,
            processing_time_ms=elapsed_ms,
        )

    async def register_face(
        self,
        image_bytes: bytes,
        person_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
    ) -> Tuple[bool, str, Optional[float], Optional[Dict[str, Any]]]:
        """
        Registers a new face profile for a person in an organization:
        1. Validates image dimensions, lighting, contrast, and blur.
        2. Enforces strict requirement of exactly one face in the image.
        3. Verifies passive liveness / anti-spoofing to reject screen replays or photo prints.
        4. Generates a 128-d face embedding vector.
        5. Saves original photo to disk.
        6. Persists FaceProfile record and updates Person.face_registered.
        7. Invalidates recognizer memory cache.

        Returns:
            (success: bool, message: str, quality_score: float, face_profile_dict: dict)
        """
        person_uuid = uuid.UUID(str(person_id)) if isinstance(person_id, str) else person_id
        org_uuid = uuid.UUID(str(org_id)) if isinstance(org_id, str) else org_id

        # 1. Fetch Person record
        stmt = select(Person).where(Person.id == person_uuid, Person.organization_id == org_uuid)
        result = await db.execute(stmt)
        person = result.scalar_one_or_none()
        if not person:
            return False, f"Person {person_id} not found in organization {org_id}", None, None

        # 2. Decode image
        loop = asyncio.get_running_loop()
        try:
            image_rgb = await loop.run_in_executor(None, load_image_from_bytes, image_bytes)
        except Exception as e:
            return False, f"Failed to decode image: {str(e)}", None, None

        # 3. Validate image quality
        is_valid, quality_score, issues = await loop.run_in_executor(
            None, validate_image_quality, image_rgb
        )
        if not is_valid:
            issue_msg = "; ".join(issues)
            return False, f"Image quality check failed: {issue_msg}", quality_score, None

        # 4. Check face count (must have exactly 1 face)
        faces = await loop.run_in_executor(None, detect_faces, image_rgb)
        if len(faces) == 0:
            return False, "No face detected in the image. Please look directly at camera.", quality_score, None
        if len(faces) > 1:
            return False, f"Multiple faces detected ({len(faces)}). Registration image must contain only one face.", quality_score, None

        face_location = faces[0]

        # 5. Anti-spoofing check
        is_live, liveness_score, _ = await loop.run_in_executor(
            None, detect_liveness, image_rgb, face_location, 0.45, False
        )
        if not is_live:
            return False, "Anti-spoofing check failed. Image appears to be a screen replay or photo print.", quality_score, None

        # 6. Generate 128-d embedding
        embedding = await loop.run_in_executor(
            None, generate_embedding, image_rgb, face_location, 2
        )
        if embedding is None:
            return False, "Failed to compute facial embedding vector from face.", quality_score, None

        serialized_encoding = serialize_embedding(embedding)

        # 7. Save photo to storage directory
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{org_uuid}_{person_uuid}_{timestamp_str}.jpg"
        file_path = os.path.join(self.faces_dir, filename)

        def save_file():
            pil_img = Image.fromarray(image_rgb)
            pil_img.save(file_path, "JPEG", quality=92)

        await loop.run_in_executor(None, save_file)
        image_url = f"/uploads/faces/{filename}"

        # 8. Insert or update FaceProfile
        profile_stmt = select(FaceProfile).where(
            FaceProfile.person_id == person_uuid,
            FaceProfile.organization_id == org_uuid,
        )
        profile_result = await db.execute(profile_stmt)
        face_profile = profile_result.scalar_one_or_none()

        if face_profile:
            # Remove old file if it exists
            old_url = face_profile.image_url
            if old_url:
                old_path = os.path.join(settings.UPLOAD_DIR, old_url.lstrip("/uploads/"))
                if os.path.exists(old_path) and old_path != file_path:
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            face_profile.encoding = serialized_encoding
            face_profile.image_url = image_url
            face_profile.quality_score = quality_score
            face_profile.updated_at = utcnow()
        else:
            face_profile = FaceProfile(
                person_id=person_uuid,
                organization_id=org_uuid,
                encoding=serialized_encoding,
                image_url=image_url,
                quality_score=quality_score,
                registered_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(face_profile)

        # 9. Update Person status
        person.face_registered = FaceRegStatus.REGISTERED
        person.profile_photo_url = image_url
        person.updated_at = utcnow()

        await db.commit()
        await db.refresh(face_profile)

        # 10. Invalidate recognizer memory cache
        self.recognizer.invalidate_org_cache(org_uuid)

        profile_dict = {
            "id": str(face_profile.id),
            "person_id": str(face_profile.person_id),
            "organization_id": str(face_profile.organization_id),
            "image_url": face_profile.image_url,
            "quality_score": face_profile.quality_score,
            "registered_at": face_profile.registered_at.isoformat() if face_profile.registered_at else None,
        }

        return True, "Face registered successfully", quality_score, profile_dict

    async def update_face(
        self,
        image_bytes: bytes,
        person_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
    ) -> Tuple[bool, str, Optional[float], Optional[Dict[str, Any]]]:
        """
        Updates an existing face profile. Delegates to register_face which updates
        the database record and replaces the image.
        """
        return await self.register_face(
            image_bytes=image_bytes,
            person_id=person_id,
            org_id=org_id,
            db=db,
        )

    async def delete_face(
        self,
        person_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
    ) -> Tuple[bool, str]:
        """
        Deletes a person's registered face profile and cleans up storage.
        Updates person's face_registered status to NOT_REGISTERED.
        """
        person_uuid = uuid.UUID(str(person_id)) if isinstance(person_id, str) else person_id
        org_uuid = uuid.UUID(str(org_id)) if isinstance(org_id, str) else org_id

        stmt = select(FaceProfile).where(
            FaceProfile.person_id == person_uuid,
            FaceProfile.organization_id == org_uuid,
        )
        result = await db.execute(stmt)
        face_profile = result.scalar_one_or_none()

        if not face_profile:
            return False, f"Face profile not found for person {person_id}"

        # Remove image file from disk
        if face_profile.image_url:
            file_name = os.path.basename(face_profile.image_url)
            file_path = os.path.join(self.faces_dir, file_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(f"Failed to delete face profile file {file_path}: {e}")

        # Delete FaceProfile entity
        await db.delete(face_profile)

        # Update Person
        p_stmt = select(Person).where(Person.id == person_uuid, Person.organization_id == org_uuid)
        p_res = await db.execute(p_stmt)
        person = p_res.scalar_one_or_none()
        if person:
            person.face_registered = FaceRegStatus.NOT_REGISTERED
            person.updated_at = utcnow()

        await db.commit()

        # Invalidate recognizer cache
        self.recognizer.invalidate_org_cache(org_uuid)

        return True, "Face profile deleted successfully"


# Global singleton instance of RecognitionPipeline
pipeline = RecognitionPipeline()
