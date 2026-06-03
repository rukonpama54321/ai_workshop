"""Orchestrates document processing for a claim."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Claim, ClaimDocument, ClaimLineItem, ClaimStatus, ExtractionField
from app.pipeline.claim_validator import validate_claim
from app.pipeline.classifier import classify_document
from app.pipeline.extractor import extract_entities
from app.pipeline.ingest import extract_text_from_file_with_meta


async def process_claim(db: Session, claim: Claim, upload_dir: Path) -> Claim:
    if not claim.user:
        from app.models import User

        claim.user = db.query(User).filter(User.id == claim.user_id).first()

    claim.status = ClaimStatus.PROCESSING
    db.commit()

    combined_text = ""
    for doc in claim.documents:
        file_path = upload_dir / doc.storage_path
        text, ocr_method, ocr_error = extract_text_from_file_with_meta(file_path)
        doc_type, confidence = classify_document(text)
        doc.doc_type = doc_type
        combined_text += f"\n--- {doc.filename} ---\n{text}\n"

        db.add(
            ExtractionField(
                claim_id=claim.id,
                field_name=f"doc_type:{doc.filename}",
                value=doc_type,
                confidence=confidence,
                page_num=1,
                method="keyword_classifier",
                review_required=confidence < 0.7,
            )
        )
        db.add(
            ExtractionField(
                claim_id=claim.id,
                field_name=f"ocr:{doc.filename}",
                value=text[:500] if text else None,
                confidence=0.9 if text else None,
                page_num=1,
                method=ocr_method,
                review_required=not bool(text.strip()),
            )
        )
        if ocr_error:
            db.add(
                ExtractionField(
                    claim_id=claim.id,
                    field_name=f"ocr_error:{doc.filename}",
                    value=ocr_error,
                    confidence=None,
                    page_num=1,
                    method=ocr_method,
                    review_required=True,
                )
            )

    extracted = await extract_entities(combined_text)
    if not combined_text.strip():
        extracted.low_confidence_fields.append("no_document_text")

    user = claim.user

    from app.models import EligibilityLimit, Hospital, HospitalDiscount, Medicine

    limits = db.query(EligibilityLimit).all()
    discount_map: dict[str, float] = {}
    for h in db.query(Hospital).all():
        disc = db.query(HospitalDiscount).filter(HospitalDiscount.hospital_id == h.id).first()
        if disc:
            discount_map[h.name] = disc.discount_pct

    reimbursable = {m.name.lower() for m in db.query(Medicine).filter(Medicine.is_reimbursable.is_(True)).all()}
    non_reimbursable = {m.name.lower() for m in db.query(Medicine).filter(Medicine.is_reimbursable.is_(False)).all()}

    from datetime import date

    result = validate_claim(
        user=user,
        extracted=extracted,
        submission_date=claim.submission_date.date() if claim.submission_date else date.today(),
        eligibility_limits=limits,
        hospital_discounts=discount_map,
        reimbursable_medicines=reimbursable,
        non_reimbursable_medicines=non_reimbursable,
    )

    claim.claim_type = result.claim_type
    claim.total_claimed = result.total_claimed
    claim.total_claimable = result.total_claimable
    claim.total_deductions = result.total_deductions
    claim.summary_json = result.summary_json

    db.query(ClaimLineItem).filter(ClaimLineItem.claim_id == claim.id).delete()
    for item in result.line_items:
        db.add(
            ClaimLineItem(
                claim_id=claim.id,
                category=item.category,
                description=item.description,
                amount_claimed=item.amount_claimed,
                amount_claimable=item.amount_claimable,
                limit_applied=item.limit_applied,
                status_flag=item.status_flag,
                deduction_comment=item.deduction_comment,
                review_required=item.review_required,
            )
        )

    for field_name, value in [
        ("hospital_name", extracted.hospital_name),
        ("diagnosis", extracted.diagnosis),
        ("claim_type", extracted.claim_type),
    ]:
        db.add(
            ExtractionField(
                claim_id=claim.id,
                field_name=field_name,
                value=str(value) if value else None,
                confidence=0.8 if value else None,
                page_num=1,
                method="extractor",
                review_required=value is None,
            )
        )

    claim.status = ClaimStatus.PENDING_REVIEW if result.review_required else ClaimStatus.PENDING_SIGNOFF
    db.commit()
    db.refresh(claim)
    return claim
