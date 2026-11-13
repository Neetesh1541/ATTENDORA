import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anti_spoof import detect_liveness
from app.ai.detector import (
    detect_faces_from_frame,
    load_image_from_bytes,
    location_to_bbox,
)
from app.ai.embeddings import (
    deserialize_embedding,
    distance_to_confidence,
    find_match,
)
from app.core.config import settings
from app.models.models import FaceProfile, FaceRegStatus, Person, PersonStatus

logger = logging.getLogger(__name__)


@dataclass
class RecognitionResult:
    person_id: Optional[str]
    name: Optional[str]
    unique_id: Optional[str]
    confidence: float
    distance: float
    bbox: Dict[str, int]
    is_recognized: bool
    status: str  # "recognized", "unknown", "low_confidence", "spoof_detected"
    is_live: bool = True
    liveness_score: float = 1.0
    liveness_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FaceRecognizer:
    """
    Main face recognition engine for ATTENDORA.
    - Manages in-memory caching of organization facial embeddings with TTL.
    - Thread-safe for concurrent camera processing.
    - Tracks recognized individuals per session/camera to avoid duplicate attendance records.
    - Supports both sync CPU-bound computation and async interface for FastAPI.
    """

    def __init__(
        self,
        tolerance: Optional[float] = None,
        min_confidence: Optional[float] = None,
        model: Optional[str] = None,
        cache_ttl_seconds: int = 300,
    ):
        self.tolerance = (
            tolerance
            if tolerance is not None
            else getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.45)
        )
        self.min_confidence = (
            min_confidence
            if min_confidence is not None
            else getattr(settings, "MIN_FACE_CONFIDENCE", 0.60)
        )
        self.model = model or getattr(settings, "FACE_RECOGNITION_MODEL", "hog")
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)

        # Thread-safe cache: {org_id_str: {"loaded_at": datetime, "people": {person_id_str: {...}}}}
        self._org_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()

        # Cooldown tracker to prevent duplicate attendance marks:
        # key: "{org_id}:{camera_or_session_id}:{person_id}" -> last_seen_datetime
        self._cooldowns: Dict[str, datetime] = {}
        self._cooldown_lock = threading.RLock()

    def invalidate_org_cache(self, org_id: Optional[Union[uuid.UUID, str]] = None) -> None:
        """
        Invalidates cached embeddings for a specific organization or all organizations.
        Call this when a person registers, updates, or deletes their face profile.
        """
        with self._cache_lock:
            if org_id is not None:
                org_key = str(org_id)
                self._org_cache.pop(org_key, None)
                logger.info(f"Invalidated face recognition cache for organization {org_key}")
            else:
                self._org_cache.clear()
                logger.info("Invalidated all face recognition caches")

    def should_record_attendance(
        self,
        org_id: Union[uuid.UUID, str],
        session_or_camera_id: Union[uuid.UUID, str],
        person_id: Union[uuid.UUID, str],
        cooldown_seconds: int = 60,
    ) -> bool:
        """
        Determines if an attendance record should be marked for this person,
        or if they are within the duplicate-suppression cooldown period.
        """
        key = f"{org_id}:{session_or_camera_id}:{person_id}"
        now = datetime.now(timezone.utc)
        with self._cooldown_lock:
            last_marked = self._cooldowns.get(key)
            if last_marked is not None:
                elapsed = (now - last_marked).total_seconds()
                if elapsed < cooldown_seconds:
                    return False
            self._cooldowns[key] = now
            return True

    def reset_cooldown(
        self,
        org_id: Union[uuid.UUID, str],
        session_or_camera_id: Union[uuid.UUID, str],
        person_id: Union[uuid.UUID, str],
    ) -> None:
        """Manually clears cooldown for a specific person."""
        key = f"{org_id}:{session_or_camera_id}:{person_id}"
        with self._cooldown_lock:
            self._cooldowns.pop(key, None)

    async def load_org_embeddings(
        self,
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
        force_reload: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Loads all active, registered face embeddings for an organization.
        Utilizes an in-memory TTL cache to minimize database load during high-frequency camera streams.

        Returns:
            Dict mapping person_id (str) to:
            {
                "person_id": str,
                "name": str,
                "unique_id": str,
                "embedding": np.ndarray (128-d float64),
            }
        """
        org_key = str(org_id)
        now = datetime.now(timezone.utc)

        # Check cache under lock
        with self._cache_lock:
            cached = self._org_cache.get(org_key)
            if (
                not force_reload
                and cached is not None
                and (now - cached["loaded_at"]) < self.cache_ttl
            ):
                return cached["people"]

        # Cache miss or expired: query DB
        try:
            org_uuid = uuid.UUID(org_key) if isinstance(org_id, str) else org_id
        except ValueError:
            logger.error(f"Invalid organization UUID: {org_id}")
            return {}

        stmt = (
            select(FaceProfile, Person)
            .join(Person, FaceProfile.person_id == Person.id)
            .where(
                FaceProfile.organization_id == org_uuid,
                Person.status == PersonStatus.ACTIVE,
                Person.face_registered == FaceRegStatus.REGISTERED,
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        people_dict: Dict[str, Dict[str, Any]] = {}
        for face_profile, person in rows:
            try:
                emb = deserialize_embedding(face_profile.encoding)
                pid_str = str(person.id)
                people_dict[pid_str] = {
                    "person_id": pid_str,
                    "name": person.full_name,
                    "unique_id": person.unique_id,
                    "embedding": emb,
                }
            except Exception as e:
                logger.error(f"Failed to deserialize embedding for person {person.id}: {e}")

        with self._cache_lock:
            self._org_cache[org_key] = {
                "loaded_at": now,
                "people": people_dict,
            }

        logger.info(f"Loaded {len(people_dict)} registered faces for organization {org_key}")
        return people_dict

    def recognize_frame_sync(
        self,
        frame: np.ndarray,
        known_people: Dict[str, Dict[str, Any]],
        check_liveness: bool = True,
        is_bgr: bool = True,
    ) -> List[RecognitionResult]:
        """
        Synchronous, CPU-bound recognition pass on a single video frame or image array.
        Designed to be executed in a thread pool via asyncio.run_in_executor.

        Pipeline:
        1. Detect all faces and calculate 128-d encodings.
        2. For each face, perform passive anti-spoofing check.
        3. Match embedding against org's known faces.
        4. Classify status ("recognized", "low_confidence", "unknown", "spoof_detected").
        """
        if frame is None or frame.size == 0:
            return []

        # Detect face locations & encodings
        detected = detect_faces_from_frame(frame, model=self.model, is_bgr=is_bgr)
        if not detected:
            return []

        results: List[RecognitionResult] = []

        # Prepare known embeddings dict: {person_id: np.ndarray}
        known_embeddings = {
            pid: data["embedding"]
            for pid, data in known_people.items()
            if data.get("embedding") is not None
        }

        for location, probe_embedding in detected:
            bbox = location_to_bbox(location)

            # Liveness / Anti-spoofing check
            is_live = True
            liveness_score = 1.0
            liveness_details = None

            if check_liveness:
                is_live, liveness_score, liveness_details = detect_liveness(
                    frame=frame, face_location=location, is_bgr=is_bgr
                )

            # Identity matching
            match = find_match(
                embedding=probe_embedding,
                known_embeddings=known_embeddings,
                tolerance=self.tolerance,
            )

            if match is not None:
                matched_id, confidence, distance = match
                person_info = known_people.get(str(matched_id), {})
                name = person_info.get("name", "Unknown")
                unique_id = person_info.get("unique_id")

                if not is_live:
                    status = "spoof_detected"
                    is_recognized = False
                elif confidence >= self.min_confidence:
                    status = "recognized"
                    is_recognized = True
                else:
                    status = "low_confidence"
                    is_recognized = False

                results.append(
                    RecognitionResult(
                        person_id=str(matched_id),
                        name=name,
                        unique_id=unique_id,
                        confidence=confidence,
                        distance=round(distance, 4),
                        bbox=bbox,
                        is_recognized=is_recognized,
                        status=status,
                        is_live=is_live,
                        liveness_score=liveness_score,
                        liveness_details=liveness_details,
                    )
                )
            else:
                # Unknown face (no match within tolerance)
                results.append(
                    RecognitionResult(
                        person_id=None,
                        name="Unknown",
                        unique_id=None,
                        confidence=0.0,
                        distance=1.0,
                        bbox=bbox,
                        is_recognized=False,
                        status="unknown",
                        is_live=is_live,
                        liveness_score=liveness_score,
                        liveness_details=liveness_details,
                    )
                )

        return results

    async def recognize_frame(
        self,
        frame: np.ndarray,
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
        check_liveness: bool = True,
        is_bgr: bool = True,
    ) -> List[RecognitionResult]:
        """
        Asynchronously recognizes all faces in a video frame.
        Loads org embeddings asynchronously, then executes CPU recognition in a thread pool.
        """
        known_people = await self.load_org_embeddings(org_id, db)
        loop = asyncio.get_running_loop()

        results = await loop.run_in_executor(
            None,
            self.recognize_frame_sync,
            frame,
            known_people,
            check_liveness,
            is_bgr,
        )
        return results

    async def recognize_image(
        self,
        image_bytes: bytes,
        org_id: Union[uuid.UUID, str],
        db: AsyncSession,
        check_liveness: bool = True,
    ) -> List[RecognitionResult]:
        """
        Asynchronously decodes image bytes and performs recognition for an organization.
        """
        loop = asyncio.get_running_loop()
        frame_rgb = await loop.run_in_executor(None, load_image_from_bytes, image_bytes)
        # Note: frame_rgb is RGB, so is_bgr=False
        return await self.recognize_frame(
            frame=frame_rgb,
            org_id=org_id,
            db=db,
            check_liveness=check_liveness,
            is_bgr=False,
        )


# Global singleton instance of FaceRecognizer
face_recognizer = FaceRecognizer()
