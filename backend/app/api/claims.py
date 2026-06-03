import shutil
import uuid
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_roles
from app.config import settings
from app.database import get_db
from app.models import Claim, ClaimDocument, ClaimStatus, Feedback, User, UserRole
from app.pipeline.processor import process_claim
from app.schemas import ClaimDetail, ClaimSummary, ReviewAction

router = APIRouter(prefix="/claims", tags=["claims"])

EMPLOYEE_DELETABLE = {
    ClaimStatus.UPLOADED,
    ClaimStatus.PROCESSING,
    ClaimStatus.VALIDATED,
    ClaimStatus.PENDING_REVIEW,
    ClaimStatus.PENDING_SIGNOFF,
    ClaimStatus.REJECTED,
    ClaimStatus.NEEDS_INFO,
}


def _get_claim_or_404(db: Session, claim_id: UUID) -> Claim:
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def _assert_can_delete(claim: Claim, user: User) -> None:
    if user.role in (UserRole.REVIEWER, UserRole.ADMIN):
        return
    if claim.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your claim")
    if claim.status == ClaimStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Approved claims cannot be deleted")
    if claim.status not in EMPLOYEE_DELETABLE:
        raise HTTPException(status_code=403, detail="This claim cannot be deleted")


def _remove_claim_files(claim_id: UUID) -> None:
    claim_dir = Path(settings.upload_dir) / str(claim_id)
    if claim_dir.exists():
        shutil.rmtree(claim_dir, ignore_errors=True)


def _claim_to_summary(claim: Claim) -> ClaimSummary:
    has_flags = any(li.review_required for li in claim.line_items) or claim.status == ClaimStatus.PENDING_REVIEW
    return ClaimSummary(
        id=claim.id,
        status=claim.status,
        claim_type=claim.claim_type,
        submission_date=claim.submission_date,
        total_claimed=claim.total_claimed,
        total_claimable=claim.total_claimable,
        total_deductions=claim.total_deductions,
        employee_name=claim.user.full_name if claim.user else None,
        has_review_flags=has_flags,
    )


@router.get("", response_model=list[ClaimSummary])
def list_claims(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    q = db.query(Claim).options(joinedload(Claim.user), joinedload(Claim.line_items))
    if user.role == UserRole.EMPLOYEE:
        q = q.filter(Claim.user_id == user.id)
    claims = q.order_by(Claim.created_at.desc()).all()
    return [_claim_to_summary(c) for c in claims]


@router.get("/{claim_id}", response_model=ClaimDetail)
def get_claim(
    claim_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    claim = (
        db.query(Claim)
        .options(
            joinedload(Claim.user),
            joinedload(Claim.documents),
            joinedload(Claim.line_items),
            joinedload(Claim.extraction_fields),
        )
        .filter(Claim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if user.role == UserRole.EMPLOYEE and claim.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your claim")
    return ClaimDetail(
        **_claim_to_summary(claim).model_dump(),
        summary_json=claim.summary_json,
        reviewer_comment=claim.reviewer_comment,
        documents=claim.documents,
        line_items=claim.line_items,
        extraction_fields=claim.extraction_fields,
    )


@router.post("", response_model=ClaimSummary)
async def create_claim(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    files: list[UploadFile] = File(...),
):
    if user.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees submit claims")

    claim = Claim(user_id=user.id, status=ClaimStatus.UPLOADED)
    db.add(claim)
    db.flush()

    upload_root = Path(settings.upload_dir)
    claim_dir = upload_root / str(claim.id)
    claim_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        ext = Path(f.filename or "doc.pdf").suffix
        stored = f"{uuid.uuid4()}{ext}"
        dest = claim_dir / stored
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        db.add(
            ClaimDocument(
                claim_id=claim.id,
                filename=f.filename or stored,
                storage_path=f"{claim.id}/{stored}",
            )
        )

    db.commit()
    db.refresh(claim)
    claim = await process_claim(db, claim, upload_root)
    claim.user = user
    return _claim_to_summary(claim)


@router.post("/{claim_id}/review", response_model=ClaimDetail)
def review_claim(
    claim_id: UUID,
    action: ReviewAction,
    reviewer: Annotated[User, Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    claim = (
        db.query(Claim)
        .options(
            joinedload(Claim.user),
            joinedload(Claim.documents),
            joinedload(Claim.line_items),
            joinedload(Claim.extraction_fields),
        )
        .filter(Claim.id == claim_id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    from datetime import datetime, timezone

    claim.reviewer_comment = action.comment
    claim.reviewed_by_id = reviewer.id
    claim.reviewed_at = datetime.now(timezone.utc)

    if action.action == "approve":
        claim.status = ClaimStatus.APPROVED
    elif action.action == "reject":
        claim.status = ClaimStatus.REJECTED
    else:
        claim.status = ClaimStatus.NEEDS_INFO

    db.commit()
    db.refresh(claim)
    return ClaimDetail(
        **_claim_to_summary(claim).model_dump(),
        summary_json=claim.summary_json,
        reviewer_comment=claim.reviewer_comment,
        documents=claim.documents,
        line_items=claim.line_items,
        extraction_fields=claim.extraction_fields,
    )


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(
    claim_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    claim = _get_claim_or_404(db, claim_id)
    _assert_can_delete(claim, user)

    db.query(Feedback).filter(Feedback.claim_id == claim_id).update({Feedback.claim_id: None})
    db.delete(claim)
    db.commit()
    _remove_claim_files(claim_id)
    return None
