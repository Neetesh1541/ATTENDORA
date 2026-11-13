import logging
from typing import Any, Dict, Optional, Tuple
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


def _compute_texture_score(gray_crop: np.ndarray) -> Tuple[float, float]:
    """
    Analyzes high-frequency facial skin texture using Laplacian variance.
    Natural faces under typical webcam lighting have Laplacian variance
    between 70 and 500.

    Printed paper or heavily smoothed images have low variance (< 60).
    Screen replays with digital moiré patterns often exhibit extreme spikes (> 850).
    """
    if not CV2_AVAILABLE or cv2 is None:
        # Fallback variance computation
        dx = np.diff(gray_crop, axis=1)
        dy = np.diff(gray_crop, axis=0)
        lap_var = float(np.var(dx) + np.var(dy))
    else:
        lap_var = float(cv2.Laplacian(gray_crop, cv2.CV_64F).var())

    # Optimal range for live webcam face: 80 - 450
    if lap_var < 50.0:
        # Too blurry / flat / paper print
        score = max(0.05, lap_var / 50.0 * 0.5)
    elif lap_var > 900.0:
        # Screen moiré artifact or extreme pixel noise
        score = max(0.1, 1.0 - min(1.0, (lap_var - 900.0) / 600.0))
    elif 80.0 <= lap_var <= 450.0:
        score = 0.95
    else:
        # 50 - 80 or 450 - 900
        if lap_var < 80.0:
            score = 0.5 + (lap_var - 50.0) / 30.0 * 0.45
        else:
            score = 0.95 - (lap_var - 450.0) / 450.0 * 0.45

    return round(float(np.clip(score, 0.0, 1.0)), 3), round(lap_var, 2)


def _compute_color_score(rgb_crop: np.ndarray) -> Tuple[float, Dict[str, float]]:
    """
    Evaluates chrominance distribution in YCbCr color space.
    Genuine human skin exhibits characteristic Cr and Cb values:
    Cr: ~133 - 173, Cb: ~77 - 127.
    Screens often bleed backlight blue (elevated Cb) or saturate,
    while grayscale prints have near-zero chrominance standard deviation.
    """
    if not CV2_AVAILABLE or cv2 is None:
        # Basic RGB channel ratios
        r, g, b = rgb_crop[..., 0], rgb_crop[..., 1], rgb_crop[..., 2]
        std_r, std_g, std_b = float(np.std(r)), float(np.std(g)), float(np.std(b))
        has_color = (std_r > 10.0 and std_g > 10.0 and std_b > 10.0)
        return (0.85 if has_color else 0.2), {"std_r": std_r, "std_g": std_g, "std_b": std_b}

    ycbcr = cv2.cvtColor(rgb_crop, cv2.COLOR_RGB2YCrCb)
    y, cr, cb = cv2.split(ycbcr)

    mean_cr = float(np.mean(cr))
    mean_cb = float(np.mean(cb))
    std_cr = float(np.std(cr))
    std_cb = float(np.std(cb))

    stats = {
        "mean_cr": round(mean_cr, 2),
        "mean_cb": round(mean_cb, 2),
        "std_cr": round(std_cr, 2),
        "std_cb": round(std_cb, 2),
    }

    # Grayscale or black/white print attack check
    if std_cr < 3.0 and std_cb < 3.0:
        return 0.1, stats

    # Distance from typical human skin cluster
    ideal_cr = 150.0
    ideal_cb = 105.0
    dist_cr = abs(mean_cr - ideal_cr)
    dist_cb = abs(mean_cb - ideal_cb)

    if dist_cr < 30.0 and dist_cb < 30.0:
        score = 0.95 - (dist_cr + dist_cb) / 100.0 * 0.3
    else:
        score = max(0.1, 0.65 - (dist_cr + dist_cb) / 100.0 * 0.5)

    return round(float(np.clip(score, 0.0, 1.0)), 3), stats


def _compute_specular_score(rgb_crop: np.ndarray) -> Tuple[float, float]:
    """
    Checks for harsh glass / screen reflections (specular hotspots).
    Mobile displays and glossy photos produce localized saturated highlights
    (pure white pixels 255, 255, 255) with abrupt falloff.
    """
    # Percentage of pixels with value >= 250 in all three channels
    saturated_mask = (
        (rgb_crop[..., 0] >= 250) &
        (rgb_crop[..., 1] >= 250) &
        (rgb_crop[..., 2] >= 250)
    )
    sat_ratio = float(np.mean(saturated_mask))

    if sat_ratio > 0.08:
        # More than 8% saturated highlights indicates severe screen reflection or flash glare
        score = max(0.1, 1.0 - (sat_ratio / 0.15))
    elif sat_ratio > 0.03:
        score = 0.6
    else:
        score = 0.95

    return round(float(np.clip(score, 0.0, 1.0)), 3), round(sat_ratio, 4)


def _compute_edge_score(gray_crop: np.ndarray) -> Tuple[float, int]:
    """
    Checks for artificial rectangular borders (e.g. tablet/phone bezel, paper edge).
    """
    if not CV2_AVAILABLE or cv2 is None or gray_crop.shape[0] < 40 or gray_crop.shape[1] < 40:
        return 0.85, 0

    try:
        edges = cv2.Canny(gray_crop, 80, 180)
        # Search for long straight lines near borders
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=50, minLineLength=int(gray_crop.shape[1] * 0.6), maxLineGap=10
        )
        line_count = len(lines) if lines is not None else 0

        if line_count >= 3:
            # Strong artificial straight lines inside face crop suggests a held frame/screen
            score = 0.35
        elif line_count == 2:
            score = 0.65
        else:
            score = 0.90

        return score, line_count
    except Exception as e:
        logger.debug(f"Edge detection error: {e}")
        return 0.85, 0


def detect_liveness(
    frame: np.ndarray,
    face_location: Tuple[int, int, int, int],
    threshold: float = 0.50,
    is_bgr: bool = False,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Performs multi-cue passive anti-spoofing / liveness detection on a detected face.

    Heuristics:
    1. Facial skin texture and frequency analysis (Laplacian variance)
    2. Chrominance distribution (YCbCr skin cluster verification)
    3. Specular highlight and glass glare analysis
    4. Screen bezel and paper edge pattern detection

    Args:
        frame: Full frame image as numpy array (RGB by default, or BGR if is_bgr=True)
        face_location: (top, right, bottom, left) coordinates
        threshold: Decision threshold for liveness (default: 0.50)
        is_bgr: Set to True if input frame is OpenCV BGR format

    Returns:
        (is_live: bool, liveness_score: float [0.0 - 1.0], details: dict)
    """
    if frame is None or frame.size == 0 or not face_location:
        return False, 0.0, {"error": "Invalid frame or face location"}

    h_img, w_img = frame.shape[:2]
    top, right, bottom, left = face_location

    # Expand margin slightly (10%) to inspect immediate boundary without losing face focus
    face_w = max(1, right - left)
    face_h = max(1, bottom - top)
    margin_x = int(face_w * 0.10)
    margin_y = int(face_h * 0.10)

    y1 = max(0, top - margin_y)
    y2 = min(h_img, bottom + margin_y)
    x1 = max(0, left - margin_x)
    x2 = min(w_img, right + margin_x)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return False, 0.0, {"error": "Empty face crop"}

    # Convert to RGB if BGR
    if is_bgr and CV2_AVAILABLE and cv2 is not None:
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    else:
        rgb_crop = crop

    # Convert to Grayscale
    if CV2_AVAILABLE and cv2 is not None:
        if len(rgb_crop.shape) == 3:
            gray_crop = cv2.cvtColor(rgb_crop, cv2.COLOR_RGB2GRAY)
        else:
            gray_crop = rgb_crop
    else:
        gray_crop = np.dot(rgb_crop[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)

    # 1. Texture analysis
    texture_score, lap_var = _compute_texture_score(gray_crop)

    # 2. Chrominance analysis
    color_score, color_stats = _compute_color_score(rgb_crop)

    # 3. Specular highlights
    specular_score, sat_ratio = _compute_specular_score(rgb_crop)

    # 4. Border edges
    edge_score, line_count = _compute_edge_score(gray_crop)

    # Weighted combined liveness score
    weights = {
        "texture": 0.35,
        "color": 0.30,
        "specular": 0.20,
        "edge": 0.15,
    }

    liveness_score = (
        weights["texture"] * texture_score +
        weights["color"] * color_score +
        weights["specular"] * specular_score +
        weights["edge"] * edge_score
    )

    final_score = round(float(np.clip(liveness_score, 0.0, 1.0)), 3)
    is_live = final_score >= threshold

    details = {
        "is_live": is_live,
        "liveness_score": final_score,
        "threshold": threshold,
        "subscores": {
            "texture": texture_score,
            "color": color_score,
            "specular": specular_score,
            "edge": edge_score,
        },
        "metrics": {
            "laplacian_variance": lap_var,
            "saturated_pixel_ratio": sat_ratio,
            "straight_lines_detected": line_count,
            "color_stats": color_stats,
        },
    }

    return is_live, final_score, details
