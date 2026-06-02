"""Document ingestion utilities."""

from pathlib import Path

from pypdf import PdfReader


def count_pages(file_path: Path) -> int:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        try:
            return len(PdfReader(str(file_path)).pages)
        except Exception:
            return 1
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return 1
    if suffix == ".txt":
        return 1
    return 1


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        try:
            import pytesseract
            from PIL import Image

            return pytesseract.image_to_string(Image.open(file_path))
        except Exception:
            return ""
    return ""
