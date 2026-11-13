import base64
import io
import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)

if not FACE_RECOGNITION_AVAILABLE:
    logger.warning(
        "face_recognition library is not available. "
        "Detector will use OpenCV Haar cascades or mock fallback mode."
    )

# Cached Haar Cascade detector for fallback
_haar_cascade = None


def _get_haar_cascade():
    global _haar_cascade
    if _haar_cascade is None and CV2_AVAILABLE and cv2 is not None:
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            _haar_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception as e:
            logger.error(f"Failed to load OpenCV Haar cascade: {e}")
            _haar_cascade = None
    return _haar_cascade


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Decodes raw image bytes into an RGB numpy array (uint8).
    Supports JPEG, PNG, WebP, etc.
    """
    if not image_bytes:
        raise ValueError("Image bytes are empty")

    if CV2_AVAILABLE and cv2 is not None:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Failed to decode image with OpenCV")
        # Convert BGR to RGB
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Fallback to PIL
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(pil_img, dtype=np.uint8)


def load_image_from_base64(base64_str: str) -> np.ndarray:
    """
    Decodes a base64-encoded image string (with or without data URI prefix)
    into an RGB numpy array.
    """
    if not base64_str or not isinstance(base64_str, str):
        raise ValueError("Invalid base64 image string")

    # Strip data URI prefix if present (e.g. data:image/jpeg;base64,...)
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]

    image_bytes = base64.b64decode(base64_str)
    return load_image_from_bytes(image_bytes)


def location_to_bbox(location: Tuple[int, int, int, int]) -> Dict[str, int]:
    """
    Converts face_recognition location (top, right, bottom, left)
    to a bounding box dictionary suitable for UI overlay.
    """
    top, right, bottom, left = location
    width = max(0, right - left)
    height = max(0, bottom - top)
    return {
        "x": int(left),
        "y": int(top),
        "width": int(width),
        "height": int(height),
        "top": int(top),
        "right": int(right),
        "bottom": int(bottom),
        "left": int(left),
    }


def bbox_to_location(bbox: Dict[str, int]) -> Tuple[int, int, int, int]:
    """
    Converts UI bounding box dict or (x, y, w, h) to (top, right, bottom, left).
    """
    if "top" in bbox and "right" in bbox:
        return (int(bbox["top"]), int(bbox["right"]), int(bbox["bottom"]), int(bbox["left"]))
    x = int(bbox.get("x", 0))
    y = int(bbox.get("y", 0))
    w = int(bbox.get("width", 0))
    h = int(bbox.get("height", 0))
    return (y, x + w, y + h, x)


def enhance_lighting(rgb_image: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
    to the luminance channel of an RGB image to improve detection
    under poor or uneven lighting conditions.
    """
    if not CV2_AVAILABLE or cv2 is None:
        return rgb_image

    try:
        lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        enhanced_lab = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    except Exception as e:
        logger.debug(f"CLAHE lighting enhancement failed: {e}")
        return rgb_image


def detect_faces(
    image: np.ndarray,
    model: Optional[str] = None,
    upsample: int = 1,
    retry_enhanced: bool = True,
) -> List[Tuple[int, int, int, int]]:
    """
    Detects faces in an RGB image.
    Returns a list of face locations in (top, right, bottom, left) order.

    Handles poor lighting by attempting CLAHE enhancement if standard
    detection yields no faces.
    """
    if image is None or image.size == 0:
        return []

    detection_model = model or getattr(settings, "FACE_RECOGNITION_MODEL", "hog")

    if FACE_RECOGNITION_AVAILABLE and face_recognition is not None:
        try:
            locations = face_recognition.face_locations(
                image, number_of_times_to_upsample=upsample, model=detection_model
            )
            if locations:
                return locations

            # If no faces detected and retry_enhanced is allowed, enhance lighting and retry
            if retry_enhanced:
                enhanced = enhance_lighting(image)
                locations = face_recognition.face_locations(
                    enhanced, number_of_times_to_upsample=upsample, model=detection_model
                )
                if locations:
                    return locations

            return []
        except Exception as e:
            logger.warning(f"face_recognition.face_locations error: {e}. Trying fallback.")

    # Fallback to OpenCV Haar cascade
    if CV2_AVAILABLE and cv2 is not None:
        cascade = _get_haar_cascade()
        if cascade is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            # Try normal detection
            faces = cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            if len(faces) == 0 and retry_enhanced:
                equalized = cv2.equalizeHist(gray)
                faces = cascade.detectMultiScale(
                    equalized, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
                )

            locations = []
            for (x, y, w, h) in faces:
                locations.append((int(y), int(x + w), int(y + h), int(x)))
            return locations

    # Mock mode fallback (if neither library works, detect center area for dev/test)
    h, w = image.shape[:2]
    if h > 100 and w > 100:
        logger.warning("Using mock face detection bounding box.")
        return [(h // 4, 3 * w // 4, 3 * h // 4, w // 4)]
    return []


def detect_faces_from_frame(
    frame: np.ndarray,
    model: Optional[str] = None,
    is_bgr: bool = True,
) -> List[Tuple[Tuple[int, int, int, int], np.ndarray]]:
    """
    Detects faces in a video frame and computes their 128-d face encodings.
    Handles OpenCV BGR frames by converting to RGB.

    Returns:
        List of tuples: (face_location, face_encoding)
        where face_location is (top, right, bottom, left)
        and face_encoding is a 128-dimensional numpy array.
    """
    if frame is None or frame.size == 0:
        return []

    if is_bgr and CV2_AVAILABLE and cv2 is not None:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        rgb_frame = frame

    locations = detect_faces(rgb_frame, model=model)
    if not locations:
        return []

    results: List[Tuple[Tuple[int, int, int, int], np.ndarray]] = []

    if FACE_RECOGNITION_AVAILABLE and face_recognition is not None:
        try:
            encodings = face_recognition.face_encodings(rgb_frame, locations)
            for loc, enc in zip(locations, encodings):
                results.append((loc, np.asarray(enc, dtype=np.float64)))
            return results
        except Exception as e:
            logger.error(f"face_recognition.face_encodings error: {e}")

    # Fallback/mock encoding generation if face_recognition is unavailable
    for loc in locations:
        top, right, bottom, left = loc
        face_crop = rgb_frame[max(0, top):max(0, bottom), max(0, left):max(0, right)]
        if face_crop.size > 0:
            # Deterministic hash of face crop pixels for mock mode
            mean_vals = np.mean(face_crop, axis=(0, 1))
            seed = int(np.sum(mean_vals) * 1000) % (2**31 - 1)
            rng = np.random.RandomState(seed)
            mock_encoding = rng.randn(128).astype(np.float64)
            mock_encoding = mock_encoding / np.linalg.norm(mock_encoding)
            results.append((loc, mock_encoding))
        else:
            mock_encoding = np.zeros(128, dtype=np.float64)
            results.append((loc, mock_encoding))

    return results


def validate_image_quality(
    image: np.ndarray,
    min_width: int = 150,
    min_height: int = 150,
    min_face_size: int = 70,
) -> Tuple[bool, float, List[str]]:
    """
    Validates face image quality for profile registration:
    - Dimensions and resolution
    - Brightness and poor lighting
    - Overexposure
    - Contrast
    - Sharpness / Blur detection (Laplacian variance)
    - Face presence (must have exactly 1 face for registration)
    - Face centering and boundaries

    Returns:
        (is_valid: bool, quality_score: float [0.0 - 1.0], issues: List[str])
    """
    issues: List[str] = []
    scores: List[float] = []

    if image is None or image.size == 0:
        return False, 0.0, ["Image is empty or invalid."]

    h, w = image.shape[:2]

    # 1. Dimension check
    if w < min_width or h < min_height:
        issues.append(f"Image resolution is too low ({w}x{h}). Minimum required is {min_width}x{min_height}.")
        scores.append(0.2)
    else:
        scores.append(1.0)

    # Convert to grayscale for illumination & blur checks
    if CV2_AVAILABLE and cv2 is not None:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
    else:
        gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)

    # 2. Brightness / Lighting check
    mean_brightness = float(np.mean(gray))
    if mean_brightness < 40.0:
        issues.append(f"Image is too dark (brightness: {mean_brightness:.1f}/255). Please improve lighting.")
        brightness_score = max(0.1, mean_brightness / 40.0 * 0.5)
    elif mean_brightness > 225.0:
        issues.append(f"Image is overexposed (brightness: {mean_brightness:.1f}/255). Avoid direct harsh glare.")
        brightness_score = max(0.1, (255.0 - mean_brightness) / 30.0 * 0.5)
    else:
        # Ideal brightness is around 100 - 160
        deviation = abs(mean_brightness - 128.0) / 128.0
        brightness_score = max(0.6, 1.0 - deviation * 0.5)
    scores.append(brightness_score)

    # 3. Contrast check
    std_contrast = float(np.std(gray))
    if std_contrast < 22.0:
        issues.append(f"Image has low contrast (std: {std_contrast:.1f}). Face features may not be distinguishable.")
        contrast_score = max(0.1, std_contrast / 22.0 * 0.5)
    else:
        contrast_score = min(1.0, std_contrast / 50.0)
    scores.append(contrast_score)

    # 4. Blur / Sharpness check using Laplacian variance
    if CV2_AVAILABLE and cv2 is not None:
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < 55.0:
            issues.append(f"Image is blurry (sharpness score: {laplacian_var:.1f}). Please hold camera steady.")
            blur_score = max(0.1, laplacian_var / 55.0 * 0.5)
        else:
            blur_score = min(1.0, 0.5 + (laplacian_var / 200.0) * 0.5)
        scores.append(blur_score)
    else:
        scores.append(0.8)

    # 5. Face detection checks
    faces = detect_faces(image, upsample=1, retry_enhanced=True)
    if len(faces) == 0:
        issues.append("No face detected in the image. Please position your face clearly in frame.")
        scores.append(0.0)
        return False, 0.0, issues
    elif len(faces) > 1:
        issues.append(f"Multiple faces detected ({len(faces)}). Registration image must contain only one person.")
        scores.append(0.3)
        return False, float(np.mean(scores)), issues
    else:
        scores.append(1.0)
        # Face is exactly 1, check face size and centering
        top, right, bottom, left = faces[0]
        face_w = right - left
        face_h = bottom - top

        if face_w < min_face_size or face_h < min_face_size:
            issues.append(f"Face is too small in the frame ({face_w}x{face_h}px). Please move closer to camera.")
            scores.append(0.4)
        else:
            scores.append(1.0)

        # Check boundary cutoff
        margin = 5
        if top <= margin or left <= margin or bottom >= h - margin or right >= w - margin:
            issues.append("Face is partially cut off at image boundary. Please center your face.")
            scores.append(0.5)
        else:
            scores.append(1.0)

    final_quality_score = round(float(np.mean(scores)), 2)
    is_valid = len(issues) == 0

    return is_valid, final_quality_score, issues
