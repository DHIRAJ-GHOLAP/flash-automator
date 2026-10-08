"""Template image matching using OpenCV and Pillow."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import ImageGrab

from ..utils.logger import get_logger

logger = get_logger("image_matcher")


@dataclass
class MatchResult:
    found: bool
    confidence: float
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


class ImageMatcher:
    """Provides OpenCV-based template matching on the desktop screen."""

    @staticmethod
    def capture_screen(region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Capture the desktop screen or a specific bbox (x, y, x2, y2).
        Returns a BGR numpy array ready for OpenCV operations.
        """
        try:
            pil_img = ImageGrab.grab(bbox=region)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            # Fallback 100x100 blank canvas
            return np.zeros((100, 100, 3), dtype=np.uint8)

    @classmethod
    def find_template(
        cls,
        template_path: str | Path,
        threshold: float = 0.85,
        region: Optional[Tuple[int, int, int, int]] = None,
        screen_bgr: Optional[np.ndarray] = None,
    ) -> MatchResult:
        """Search for template image on the current screen."""
        t_path = Path(template_path)
        if not t_path.exists():
            logger.error(f"Template image not found: {template_path}")
            return MatchResult(found=False, confidence=0.0)

        template_bgr = cv2.imread(str(t_path))
        if template_bgr is None:
            logger.error(f"Failed to decode template image: {template_path}")
            return MatchResult(found=False, confidence=0.0)

        th, tw = template_bgr.shape[:2]

        if screen_bgr is None:
            screen_bgr = cls.capture_screen(region)

        sh, sw = screen_bgr.shape[:2]
        if sh < th or sw < tw:
            return MatchResult(found=False, confidence=0.0)

        # Grayscale conversion for robust matching
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        offset_x = region[0] if region else 0
        offset_y = region[1] if region else 0

        if max_val >= threshold:
            match_x = max_loc[0] + offset_x
            match_y = max_loc[1] + offset_y
            return MatchResult(
                found=True,
                confidence=float(max_val),
                x=match_x,
                y=match_y,
                width=tw,
                height=th,
            )

        return MatchResult(found=False, confidence=float(max_val))

    @classmethod
    def wait_for_image(
        cls,
        template_path: str | Path,
        timeout: float = 10.0,
        threshold: float = 0.85,
        poll_interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> MatchResult:
        """Continuously search for a template image until found or timeout expires."""
        start_time = time.time()
        last_result = MatchResult(found=False, confidence=0.0)

        while time.time() - start_time < timeout:
            last_result = cls.find_template(template_path, threshold=threshold, region=region)
            if last_result.found:
                return last_result
            time.sleep(poll_interval)

        return last_result
