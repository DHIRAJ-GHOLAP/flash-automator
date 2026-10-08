"""Screen change detector for smart waiting until animations/loads complete."""
from __future__ import annotations

import time
from typing import Optional, Tuple

import cv2
import numpy as np

from .image_matcher import ImageMatcher
from ..utils.logger import get_logger

logger = get_logger("screen_detector")


class ScreenDetector:
    """Monitors screen pixel changes over time."""

    @classmethod
    def compute_difference_ratio(cls, img1_bgr: np.ndarray, img2_bgr: np.ndarray) -> float:
        """Calculate fraction of pixels differing between two same-sized images."""
        if img1_bgr.shape != img2_bgr.shape:
            # Resize img2 to match img1
            img2_bgr = cv2.resize(img2_bgr, (img1_bgr.shape[1], img1_bgr.shape[0]))

        gray1 = cv2.cvtColor(img1_bgr, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        # Threshold difference: pixel change > 15
        _, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
        non_zero = np.count_nonzero(thresh)
        total = thresh.size
        return float(non_zero / total) if total > 0 else 0.0

    @classmethod
    def wait_for_screen_change(
        cls,
        diff_threshold: float = 0.02,
        timeout: float = 15.0,
        poll_interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> bool:
        """
        Wait until screen pixels change by more than diff_threshold compared to the initial baseline.
        Returns True if change detected, False if timeout.
        """
        baseline = ImageMatcher.capture_screen(region)
        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(poll_interval)
            current = ImageMatcher.capture_screen(region)
            ratio = cls.compute_difference_ratio(baseline, current)
            if ratio >= diff_threshold:
                logger.info(f"Screen change detected: {ratio:.4f} >= {diff_threshold}")
                return True

        logger.warning(f"Timeout waiting for screen change after {timeout}s")
        return False
