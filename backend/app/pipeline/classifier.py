"""Document classification."""

DOCUMENT_TYPES = [
    "discharge_summary",
    "hospital_bill",
    "pharmacy_invoice",
    "lab_report",
    "prescription",
    "handwritten_prescription",
    "doctors_advice",
    "discharge_sheet",
    "credit_referral_letter",
    "other",
]


def classify_document(text: str) -> tuple[str, float]:
    lower = text.lower()
    rules: list[tuple[str, list[str]]] = [
        ("discharge_summary", ["discharge summary", "discharge note"]),
        ("hospital_bill", ["hospital bill", "ip bill", "inpatient bill", "room charge", "tax invoice", "statement / tax invoice"]),
        ("pharmacy_invoice", ["pharmacy", "chemist", "medicine bill"]),
        ("lab_report", ["lab report", "pathology", "diagnostic"]),
        ("prescription", ["prescription", "rx", " prescribed "]),
        ("handwritten_prescription", ["handwritten"]),
        ("doctors_advice", ["doctor advice", "medical advice"]),
        ("discharge_sheet", ["discharge sheet"]),
        ("credit_referral_letter", ["referral", "credit letter"]),
    ]
    for doc_type, keywords in rules:
        if any(k in lower for k in keywords):
            return doc_type, 0.85
    return "other", 0.5
