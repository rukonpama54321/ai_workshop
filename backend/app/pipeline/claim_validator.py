"""Deterministic claim validation rules — not LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from app.models import EmployeeCategory, User
from app.schemas import ValidationLineItem, ValidationResult


@dataclass
class ExtractedClaimData:
    claim_type: str | None
    hospital_name: str | None
    invoice_date: date | None
    prescription_date: date | None
    discharge_date: date | None
    room_charge_per_day: float | None
    room_days: int | None
    discount_claimed_pct: float | None
    line_items: list[dict[str, Any]]
    medicines: list[dict[str, Any]]
    diagnosis: str | None
    low_confidence_fields: list[str]


def _cabin_limit(user: User, limits: list[Any]) -> tuple[float | None, bool]:
    """Return (daily limit, is_actuals)."""
    cat = user.employee_category
    jg = user.job_group.upper()
    city = user.city_class.upper()

    for lim in limits:
        if lim.employee_category != cat or lim.limit_type != "cabin_per_day":
            continue
        if lim.city_class not in (city, "YZ") and not (
            lim.city_class == "YZ" and city in ("Y", "Z")
        ):
            if lim.city_class != city:
                continue
        if lim.is_actuals:
            if cat == EmployeeCategory.MANAGEMENT and jg >= "G":
                return None, True
        if lim.job_group_min and jg < lim.job_group_min:
            continue
        if lim.job_group_max and jg > lim.job_group_max:
            continue
        return lim.limit_amount, lim.is_actuals
    return None, False


def validate_claim(
    user: User,
    extracted: ExtractedClaimData,
    submission_date: date,
    eligibility_limits: list[Any],
    hospital_discounts: dict[str, float],
    reimbursable_medicines: set[str],
    non_reimbursable_medicines: set[str],
) -> ValidationResult:
    line_items: list[ValidationLineItem] = []
    review_required = bool(extracted.low_confidence_fields)

    claim_type = extracted.claim_type or "outpatient"

    # Validity windows
    if extracted.prescription_date:
        days = (submission_date - extracted.prescription_date).days
        if days > 365:
            line_items.append(
                ValidationLineItem(
                    category="validity",
                    description="Prescription validity exceeded (> 1 year)",
                    amount_claimed=0,
                    amount_claimable=0,
                    status_flag="rejected",
                    deduction_comment=f"Prescription date {extracted.prescription_date} is older than 1 year",
                    review_required=False,
                )
            )

    ref_date = extracted.discharge_date or extracted.invoice_date
    if ref_date:
        days = (submission_date - ref_date).days
        if days > 90:
            line_items.append(
                ValidationLineItem(
                    category="validity",
                    description="Invoice/bill validity exceeded (> 3 months)",
                    amount_claimed=0,
                    amount_claimable=0,
                    status_flag="rejected",
                    deduction_comment=f"Bill/discharge date {ref_date} is older than 3 months",
                    review_required=False,
                )
            )

    # Cabin / room logic
    if extracted.room_charge_per_day is not None and extracted.room_days:
        daily_limit, is_actuals = _cabin_limit(user, eligibility_limits)
        total_claimed = extracted.room_charge_per_day * extracted.room_days
        if is_actuals:
            total_claimable = total_claimed
            comment = None
        elif daily_limit is None:
            total_claimable = 0
            comment = "Could not determine cabin limit for employee grade/city"
            review_required = True
        else:
            cap_per_day = min(extracted.room_charge_per_day, daily_limit)
            total_claimable = cap_per_day * extracted.room_days
            comment = None
            if extracted.room_charge_per_day > daily_limit:
                comment = (
                    f"Room charge ₹{extracted.room_charge_per_day:.0f}/day exceeds limit "
                    f"₹{daily_limit:.0f}/day; claimable capped"
                )
        line_items.append(
            ValidationLineItem(
                category="cabin",
                description=f"Room charges ({extracted.room_days} days @ ₹{extracted.room_charge_per_day:.0f}/day)",
                amount_claimed=total_claimed,
                amount_claimable=total_claimable,
                limit_applied=daily_limit,
                status_flag="capped" if comment else "ok",
                deduction_comment=comment,
                review_required=daily_limit is None,
            )
        )

    # Hospital discount check
    if extracted.hospital_name and extracted.discount_claimed_pct is not None:
        expected = None
        for name, pct in hospital_discounts.items():
            if name.lower() in extracted.hospital_name.lower():
                expected = pct
                break
        if expected is None:
            line_items.append(
                ValidationLineItem(
                    category="discount",
                    description=f"Hospital discount check — {extracted.hospital_name}",
                    amount_claimed=extracted.discount_claimed_pct,
                    amount_claimable=extracted.discount_claimed_pct,
                    status_flag="review",
                    deduction_comment="Hospital not found in empanelled discount list",
                    review_required=True,
                )
            )
            review_required = True
        elif abs(expected - extracted.discount_claimed_pct) > 0.5:
            line_items.append(
                ValidationLineItem(
                    category="discount",
                    description=f"Corporate discount — {extracted.hospital_name}",
                    amount_claimed=extracted.discount_claimed_pct,
                    amount_claimable=expected,
                    status_flag="mismatch",
                    deduction_comment=(
                        f"Claimed discount {extracted.discount_claimed_pct}% "
                        f"≠ expected {expected}%"
                    ),
                    review_required=True,
                )
            )
            review_required = True
        else:
            line_items.append(
                ValidationLineItem(
                    category="discount",
                    description=f"Corporate discount verified — {extracted.hospital_name}",
                    amount_claimed=extracted.discount_claimed_pct,
                    amount_claimable=extracted.discount_claimed_pct,
                    status_flag="ok",
                )
            )

    # Generic bill line items from extraction
    for item in extracted.line_items:
        claimed = float(item.get("amount", 0))
        line_items.append(
            ValidationLineItem(
                category=item.get("category", "other"),
                description=item.get("description", "Line item"),
                amount_claimed=claimed,
                amount_claimable=claimed,
                status_flag="ok",
            )
        )

    # Medicine validation
    for med in extracted.medicines:
        name = (med.get("name") or "").strip()
        amount = float(med.get("amount", 0))
        normalized = name.lower()
        status_flag = "ok"
        claimable = amount
        comment = None
        med_review = False

        if not name:
            status_flag = "unknown"
            claimable = 0
            comment = "Medicine name could not be read"
            med_review = True
        elif normalized in non_reimbursable_medicines:
            status_flag = "non_reimbursable"
            claimable = 0
            comment = f"{name} is on the non-reimbursable list"
        elif normalized not in reimbursable_medicines:
            status_flag = "requires_review"
            med_review = True
            comment = f"{name} not matched to reimbursable list — requires review"
        review_required = review_required or med_review

        line_items.append(
            ValidationLineItem(
                category="medicine",
                description=name or "Unknown medicine",
                amount_claimed=amount,
                amount_claimable=claimable,
                status_flag=status_flag,
                deduction_comment=comment,
                review_required=med_review,
            )
        )

    total_claimed = sum(i.amount_claimed for i in line_items if i.category not in ("validity",))
    total_claimable = sum(i.amount_claimable for i in line_items if i.status_flag != "rejected")
    total_deductions = max(0, total_claimed - total_claimable)

    summary = {
        "claim_type": claim_type,
        "employee_category": user.employee_category.value,
        "job_group": user.job_group,
        "city_class": user.city_class,
        "diagnosis": extracted.diagnosis,
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "line_item_count": len(line_items),
    }

    return ValidationResult(
        claim_type=claim_type,
        total_claimed=round(total_claimed, 2),
        total_claimable=round(total_claimable, 2),
        total_deductions=round(total_deductions, 2),
        line_items=line_items,
        review_required=review_required,
        summary_json=summary,
    )
