"""
ATTENDORA AI Face Recognition Engine
"""

from app.ai.detector import (
    detect_faces,
    detect_faces_from_frame,
    validate_image_quality,
    location_to_bbox,
    bbox_to_location,
    load_image_from_bytes,
    load_image_from_base64,
)
from app.ai.embeddings import (
    generate_embedding,
    serialize_embedding,
    deserialize_embedding,
    compare_embeddings,
    distance_to_confidence,
    find_match,
    batch_compare,
)
from app.ai.anti_spoof import detect_liveness
from app.ai.recognizer import (
    FaceRecognizer,
    RecognitionResult,
    face_recognizer,
)
from app.ai.pipeline import (
    RecognitionPipeline,
    PipelineResult,
    pipeline,
)

__all__ = [
    "detect_faces",
    "detect_faces_from_frame",
    "validate_image_quality",
    "location_to_bbox",
    "bbox_to_location",
    "load_image_from_bytes",
    "load_image_from_base64",
    "generate_embedding",
    "serialize_embedding",
    "deserialize_embedding",
    "compare_embeddings",
    "distance_to_confidence",
    "find_match",
    "batch_compare",
    "detect_liveness",
    "FaceRecognizer",
    "RecognitionResult",
    "face_recognizer",
    "RecognitionPipeline",
    "PipelineResult",
    "pipeline",
]
