"""Entity extraction — LLM with regex fallback for workshop."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

import httpx

from app.config import settings
from app.pipeline.claim_validator import ExtractedClaimData


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _regex_fallback(text: str) -> dict[str, Any]:
    amount_match = re.search(
        r"(?:total due|total|amount|bill)[:\s]*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I
    )
    hospital_match = re.search(
        r"(?:hospital|clinic|medical centre|medical center|associates)[:\s]*([A-Za-z0-9\s&.'-]+)",
        text,
        re.I,
    )
    provider_match = re.search(
        r"^([A-Za-z0-9\s&.'-]+(?:Associates|Hospital|Clinic|Medical|Health))",
        text,
        re.I | re.M,
    )
    discount_match = re.search(r"discount[:\s]*([\d.]+)\s*%", text, re.I)
    room_match = re.search(r"room[:\s]*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)
    icd_match = re.search(r"\b([A-Z]\d{2}(?:\.\d+)?)\b", text)

    medicines = []
    for m in re.finditer(r"(paracetamol|amoxicillin|metformin|azithromycin|crocin|P500)", text, re.I):
        medicines.append({"name": m.group(1).lower(), "amount": 0})

    hospital_name = None
    if hospital_match:
        hospital_name = hospital_match.group(1).strip()[:120]
    elif provider_match:
        hospital_name = provider_match.group(1).strip()[:120]
    else:
        first_line = text.strip().split("\n")[0] if text.strip() else ""
        if re.search(r"associates|hospital|clinic|medical", first_line, re.I):
            hospital_name = first_line.strip()[:120]

    line_items = []
    if amount_match:
        line_items.append(
            {
                "category": "other",
                "description": "Extracted bill total",
                "amount": float(amount_match.group(1).replace(",", "")),
            }
        )

    return {
        "claim_type": "inpatient" if re.search(r"admission|discharge|in hosp\?\s*y", text, re.I) else "outpatient",
        "hospital_name": hospital_name,
        "invoice_date": None,
        "prescription_date": None,
        "discharge_date": None,
        "room_charge_per_day": float(room_match.group(1).replace(",", "")) if room_match else None,
        "room_days": 1 if room_match else None,
        "discount_claimed_pct": float(discount_match.group(1)) if discount_match else None,
        "line_items": line_items,
        "medicines": medicines,
        "diagnosis": icd_match.group(1) if icd_match else None,
        "low_confidence_fields": [] if amount_match else ["invoice_date", "total_amount"],
    }


async def _llm_extract(text: str) -> dict[str, Any] | None:
    prompt = f"""Extract medical claim fields from this document text as JSON only.
Use null for missing values. Never invent amounts.
Fields: claim_type (inpatient/outpatient), hospital_name, invoice_date (YYYY-MM-DD),
prescription_date, discharge_date, room_charge_per_day, room_days, discount_claimed_pct,
diagnosis, line_items (array of category, description, amount), medicines (array of name, amount).

Document:
{text[:8000]}
"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/api/generate",
                json={"model": settings.llm_model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
    except Exception:
        return None
    return None


async def extract_entities(text: str) -> ExtractedClaimData:
    data = await _llm_extract(text)
    if not data:
        data = _regex_fallback(text)
        method = "regex_fallback"
    else:
        method = "ollama"

    low_conf = list(data.get("low_confidence_fields") or [])
    if method == "regex_fallback":
        low_conf.append("extraction_method")

    return ExtractedClaimData(
        claim_type=data.get("claim_type"),
        hospital_name=data.get("hospital_name"),
        invoice_date=_parse_date(data.get("invoice_date")),
        prescription_date=_parse_date(data.get("prescription_date")),
        discharge_date=_parse_date(data.get("discharge_date")),
        room_charge_per_day=data.get("room_charge_per_day"),
        room_days=data.get("room_days"),
        discount_claimed_pct=data.get("discount_claimed_pct"),
        line_items=data.get("line_items") or [],
        medicines=data.get("medicines") or [],
        diagnosis=data.get("diagnosis"),
        low_confidence_fields=low_conf,
    )


def extraction_method_label() -> str:
    return "ollama+regex"
