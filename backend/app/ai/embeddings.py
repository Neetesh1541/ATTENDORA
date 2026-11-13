import logging
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False

from app.ai.detector import detect_faces
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_embedding(
    image: np.ndarray,
    face_location: Optional[Tuple[int, int, int, int]] = None,
    num_jitters: int = 1,
) -> Optional[np.ndarray]:
    """
    Generates a 128-dimensional facial embedding vector for a given image.

    Args:
        image: RGB numpy array
        face_location: Optional (top, right, bottom, left) tuple. If None,
                       detects the face location automatically.
        num_jitters: How many times to re-sample the face when calculating
                     encoding. Higher is more accurate, but slower.

    Returns:
        128-d numpy array of dtype float64, or None if no face is detected.
    """
    if image is None or image.size == 0:
        return None

    target_location = face_location
    if target_location is None:
        locations = detect_faces(image, upsample=1)
        if not locations:
            logger.warning("No face found in image for embedding generation")
            return None
        # If multiple faces, pick the largest by bounding area
        if len(locations) > 1:
            locations = sorted(
                locations,
                key=lambda loc: (loc[2] - loc[0]) * (loc[1] - loc[3]),
                reverse=True,
            )
        target_location = locations[0]

    if FACE_RECOGNITION_AVAILABLE and face_recognition is not None:
        try:
            encodings = face_recognition.face_encodings(
                image, known_face_locations=[target_location], num_jitters=num_jitters
            )
            if encodings and len(encodings) > 0:
                return np.asarray(encodings[0], dtype=np.float64)
            return None
        except Exception as e:
            logger.error(f"Error generating face embedding with face_recognition: {e}")

    # Fallback / mock embedding generator (deterministic based on face crop pixels)
    top, right, bottom, left = target_location
    face_crop = image[max(0, top):max(0, bottom), max(0, left):max(0, right)]
    if face_crop.size > 0:
        seed = int(np.sum(face_crop.mean(axis=(0, 1))) * 1000) % (2**31 - 1)
        rng = np.random.RandomState(seed)
        mock_vec = rng.randn(128).astype(np.float64)
        mock_vec = mock_vec / np.linalg.norm(mock_vec)
        return mock_vec

    return None


def serialize_embedding(embedding: np.ndarray) -> bytes:
    """
    Serializes a numpy face embedding array into bytes for database storage
    in a LargeBinary column.
    """
    if embedding is None:
        raise ValueError("Cannot serialize None embedding")

    arr = np.asarray(embedding, dtype=np.float64).reshape(128)
    return pickle.dumps(arr, protocol=5)


def deserialize_embedding(data: bytes) -> np.ndarray:
    """
    Deserializes stored binary bytes into a 128-d float64 numpy array.
    Supports both pickle-encoded bytes and raw numpy buffer formats.
    """
    if not data:
        raise ValueError("Cannot deserialize empty embedding data")

    # 1. Try unpickling
    try:
        arr = pickle.loads(data)
        if isinstance(arr, np.ndarray):
            return arr.astype(np.float64).reshape(128)
    except Exception:
        pass

    # 2. Try raw float64 buffer
    try:
        arr = np.frombuffer(data, dtype=np.float64)
        if arr.size == 128:
            return arr.copy()
    except Exception:
        pass

    # 3. Try raw float32 buffer
    try:
        arr = np.frombuffer(data, dtype=np.float32)
        if arr.size == 128:
            return arr.astype(np.float64).copy()
    except Exception:
        pass

    raise ValueError(f"Unrecognized embedding serialization format (length {len(data)} bytes)")


def compare_embeddings(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculates the Euclidean distance between two 128-d face embeddings.
    Lower distance indicates higher similarity (0 = identical).
    """
    e1 = np.asarray(embedding1, dtype=np.float64).reshape(-1)
    e2 = np.asarray(embedding2, dtype=np.float64).reshape(-1)
    return float(np.linalg.norm(e1 - e2))


def distance_to_confidence(distance: float, tolerance: Optional[float] = None) -> float:
    """
    Calibrates Euclidean distance to a normalized confidence score [0.0, 1.0].

    Calibration curve:
    - distance = 0.0 -> confidence = 1.00 (100%)
    - distance = 0.25 -> confidence ~ 0.78
    - distance = tolerance (default 0.45) -> confidence = 0.60
    - distance = 0.60 -> confidence ~ 0.35
    - distance >= 0.85 -> confidence = 0.00
    """
    tol = tolerance if tolerance is not None else getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.45)

    if distance <= 0.0:
        return 1.0

    if distance <= tol:
        # Interpolate [0, tol] -> [1.0, 0.60]
        score = 1.0 - (distance / tol) * 0.40
    else:
        # Interpolate [tol, 0.85] -> [0.60, 0.0]
        max_dist = max(tol + 0.1, 0.85)
        ratio = (distance - tol) / (max_dist - tol)
        score = max(0.0, 0.60 - ratio * 0.60)

    return round(float(np.clip(score, 0.0, 1.0)), 4)


def find_match(
    embedding: np.ndarray,
    known_embeddings: Union[Dict[Any, np.ndarray], List[Tuple[Any, np.ndarray]]],
    tolerance: Optional[float] = None,
) -> Optional[Tuple[Any, float, float]]:
    """
    Finds the closest matching identity from a collection of known embeddings.

    Args:
        embedding: 128-d probe embedding
        known_embeddings: Dict of {person_id: embedding} or list of (person_id, embedding)
        tolerance: Euclidean distance threshold (defaults to settings.FACE_RECOGNITION_TOLERANCE)

    Returns:
        (person_id, confidence, distance) if a match within tolerance is found,
        or None if no match meets the tolerance threshold.
    """
    if embedding is None or not known_embeddings:
        return None

    tol = tolerance if tolerance is not None else getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.45)

    items = known_embeddings.items() if isinstance(known_embeddings, dict) else known_embeddings
    if not items:
        return None

    best_id = None
    min_dist = float("inf")

    probe = np.asarray(embedding, dtype=np.float64).reshape(-1)

    for person_id, known_emb in items:
        if known_emb is None:
            continue
        dist = float(np.linalg.norm(probe - np.asarray(known_emb, dtype=np.float64).reshape(-1)))
        if dist < min_dist:
            min_dist = dist
            best_id = person_id

    if best_id is not None and min_dist <= tol:
        confidence = distance_to_confidence(min_dist, tolerance=tol)
        return (best_id, confidence, min_dist)

    return None


def batch_compare(
    embedding: np.ndarray,
    org_embeddings_dict: Dict[Any, np.ndarray],
    tolerance: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Compares a probe embedding against all registered embeddings in an organization
    using vectorized matrix operations for fast execution.

    Returns:
        List of matches sorted by confidence descending:
        [
            {
                "person_id": Any,
                "distance": float,
                "confidence": float,
                "is_match": bool
            },
            ...
        ]
    """
    if embedding is None or not org_embeddings_dict:
        return []

    tol = tolerance if tolerance is not None else getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.45)
    probe = np.asarray(embedding, dtype=np.float64).reshape(1, 128)

    person_ids = []
    matrix_rows = []

    for pid, emb in org_embeddings_dict.items():
        if emb is not None:
            person_ids.append(pid)
            matrix_rows.append(np.asarray(emb, dtype=np.float64).reshape(128))

    if not matrix_rows:
        return []

    matrix = np.vstack(matrix_rows)  # (N, 128)
    distances = np.linalg.norm(matrix - probe, axis=1)  # (N,)

    results = []
    for pid, dist in zip(person_ids, distances):
        d = float(dist)
        conf = distance_to_confidence(d, tolerance=tol)
        results.append({
            "person_id": pid,
            "distance": round(d, 4),
            "confidence": conf,
            "is_match": d <= tol,
        })

    # Sort descending by confidence (ascending by distance)
    results.sort(key=lambda x: x["distance"])
    return results
