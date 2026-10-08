"""Recognition package for image matching, screen change detection, and OCR."""
from .image_matcher import ImageMatcher, MatchResult
from .screen_detector import ScreenDetector
from .ocr import OCREngine

__all__ = ["ImageMatcher", "MatchResult", "ScreenDetector", "OCREngine"]
