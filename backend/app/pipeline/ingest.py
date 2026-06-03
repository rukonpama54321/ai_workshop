"""Document ingestion utilities."""

import logging
import shutil
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_easyocr_reader = None


def _configure_tesseract() -> bool:
    try:
        import pytesseract

        if shutil.which("tesseract"):
            return True
        for candidate in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if Path(candidate).exists():
                pytesseract.pytesseract.tesseract_cmd = candidate
                return True
    except Exception as exc:
        logger.warning("Tesseract unavailable: %s", exc)
    return False


def _ocr_with_tesseract(file_path: Path) -> str:
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(file_path))


def _ocr_with_easyocr(file_path: Path) -> str:
    global _easyocr_reader
    import easyocr

    if _easyocr_reader is None:
        logger.info("Initializing EasyOCR (first run may download models)...")
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    lines = _easyocr_reader.readtext(str(file_path), detail=0, paragraph=True)
    return "\n".join(lines)


def extract_text_from_image(file_path: Path) -> tuple[str, str, str | None]:
    """Return (text, method, error)."""
    if _configure_tesseract():
        try:
            text = _ocr_with_tesseract(file_path)
            if text.strip():
                return text.strip(), "tesseract", None
        except Exception as exc:
            logger.warning("Tesseract OCR failed for %s: %s", file_path.name, exc)

    try:
        text = _ocr_with_easyocr(file_path)
        if text.strip():
            return text.strip(), "easyocr", None
        return "", "easyocr", "OCR returned empty text"
    except Exception as exc:
        logger.exception("EasyOCR failed for %s", file_path.name)
        return "", "none", str(exc)


def count_pages(file_path: Path) -> int:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        try:
            return len(PdfReader(str(file_path)).pages)
        except Exception:
            return 1
    if suffix in IMAGE_SUFFIXES or suffix == ".txt":
        return 1
    return 1


def extract_text_from_file(file_path: Path) -> str:
    text, _, _ = extract_text_from_file_with_meta(file_path)
    return text


def extract_text_from_file_with_meta(file_path: Path) -> tuple[str, str, str | None]:
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore"), "plain_text", None
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, "pdf_text", None if text.strip() else "PDF has no extractable text"
        except Exception as exc:
            return "", "pdf_text", str(exc)
    if suffix in IMAGE_SUFFIXES:
        return extract_text_from_image(file_path)
    return "", "unknown", f"Unsupported file type: {suffix}"
