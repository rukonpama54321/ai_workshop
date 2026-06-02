"""Extract master data from compensation PDF manuals into CSV (workshop script).

Usage:
  python scripts/extract_master_data.py --manual management --pdf path/to/manual.pdf
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore


def extract_text(pdf_path: Path) -> str:
    if PdfReader is None:
        raise SystemExit("Install pypdf: pip install pypdf")
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", choices=["management", "non_management"], required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("seed/extracted_limits.csv"))
    args = parser.parse_args()

    text = extract_text(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Workshop stub: writes placeholder row; replace with LLM-assisted parsing in exercise
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "employee_category",
                "limit_type",
                "city_class",
                "job_group_min",
                "job_group_max",
                "limit_amount",
                "is_actuals",
                "notes",
            ],
        )
        writer.writeheader()
        if args.manual == "non_management":
            writer.writerow(
                {
                    "employee_category": "non_management",
                    "limit_type": "cabin_per_day",
                    "city_class": "X",
                    "job_group_min": "",
                    "job_group_max": "",
                    "limit_amount": "4500",
                    "is_actuals": "false",
                    "notes": "From Non-Mgmt Table 16 — run full LLM extract for complete set",
                }
            )
        else:
            writer.writerow(
                {
                    "employee_category": "management",
                    "limit_type": "cabin_per_day",
                    "city_class": "X",
                    "job_group_min": "02",
                    "job_group_max": "F",
                    "limit_amount": "8500",
                    "is_actuals": "false",
                    "notes": "From Mgmt Table 11 — run full LLM extract for complete set",
                }
            )

    preview = args.out.with_suffix(".txt")
    preview.write_text(text[:5000], encoding="utf-8")
    print(f"Wrote stub CSV to {args.out} and text preview to {preview}")


if __name__ == "__main__":
    main()
