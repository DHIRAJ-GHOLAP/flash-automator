"""Modular, optional OCR engine using pytesseract."""
from __future__ import annotations

import shutil
from typing import Optional, Tuple

from PIL import ImageGrab

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger("ocr")


class OCREngine:
    """Provides optional OCR text extraction with graceful fallback."""

    _pytesseract = None
    _is_available: Optional[bool] = None

    @classmethod
    def check_availability(cls) -> bool:
        """Check if pytesseract and tesseract executable are installed and accessible."""
        if cls._is_available is not None:
            return cls._is_available

        try:
            import pytesseract

            cls._pytesseract = pytesseract

            # Check custom configured path or system PATH
            cfg = get_config()
            if cfg.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_cmd

            # Test if tesseract executable exists
            tess_cmd = pytesseract.pytesseract.tesseract_cmd
            is_installed = bool(shutil.which(tess_cmd))
            cls._is_available = is_installed
            if not is_installed:
                logger.info(
                    "Tesseract binary not found in PATH or config. OCR features will be disabled."
                )
        except Exception as e:
            logger.info(f"Pytesseract unavailable: {e}")
            cls._is_available = False

        return cls._is_available

    @classmethod
    def extract_text(
        cls,
        region: Optional[Tuple[int, int, int, int]] = None,
        lang: str = "eng",
    ) -> str:
        """Extract text from the screen or region via OCR."""
        if not cls.check_availability() or cls._pytesseract is None:
            logger.warning("OCR requested but Tesseract is not available.")
            return ""

        try:
            pil_img = ImageGrab.grab(bbox=region)
            text = cls._pytesseract.image_to_string(pil_img, lang=lang)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
