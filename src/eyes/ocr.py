"""OCR utilities for text extraction from images."""

from __future__ import annotations

from PIL import Image

_HAS_TESSERACT = False
try:
    import pytesseract

    _HAS_TESSERACT = True
except ImportError:
    pass


def extract_text(img: Image.Image, region: dict | None = None) -> str:
    if not _HAS_TESSERACT:
        raise RuntimeError(
            "pytesseract is required for OCR. "
            "Install with: pip install eyes-mcp[ocr]"
        )
    if region:
        x, y = region["x"], region["y"]
        w, h = region["width"], region["height"]
        img = img.crop((x, y, x + w, y + h))
    text: str = pytesseract.image_to_string(img)
    return text.strip()
