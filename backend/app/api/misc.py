from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models import Feedback, User, UserRole
from app.schemas import FeedbackCreate

router = APIRouter(tags=["misc"])


@router.post("/feedback")
def submit_feedback(
    body: FeedbackCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    fb = Feedback(
        user_id=user.id,
        feedback_type=body.feedback_type,
        title=body.title,
        description=body.description,
        claim_id=body.claim_id,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "id": str(fb.id)}


@router.get("/review/queue")
def review_queue(
    _: Annotated[User, Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Claim, ClaimStatus

    claims = (
        db.query(Claim)
        .filter(Claim.status.in_([ClaimStatus.PENDING_REVIEW, ClaimStatus.PENDING_SIGNOFF]))
        .order_by(Claim.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(c.id),
            "status": c.status.value,
            "total_claimable": c.total_claimable,
            "employee_id": str(c.user_id),
            "claim_type": c.claim_type,
        }
        for c in claims
    ]


@router.get("/health")
def health():
    return {"status": "ok"}
