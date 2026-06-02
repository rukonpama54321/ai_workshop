from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import ClaimStatus, EmployeeCategory, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: UUID
    username: str
    role: UserRole
    employee_id: str
    full_name: str
    job_group: str
    designation: str
    city_class: str
    employee_category: EmployeeCategory
    employment_status: str

    model_config = {"from_attributes": True}


class ClaimDocumentOut(BaseModel):
    id: UUID
    filename: str
    doc_type: str | None
    page_count: int

    model_config = {"from_attributes": True}


class ExtractionFieldOut(BaseModel):
    field_name: str
    value: str | None
    confidence: float | None
    page_num: int | None
    method: str
    review_required: bool

    model_config = {"from_attributes": True}


class ClaimLineItemOut(BaseModel):
    id: UUID
    category: str
    description: str
    amount_claimed: float
    amount_claimable: float
    limit_applied: float | None
    status_flag: str
    deduction_comment: str | None
    review_required: bool

    model_config = {"from_attributes": True}


class ClaimSummary(BaseModel):
    id: UUID
    status: ClaimStatus
    claim_type: str | None
    submission_date: datetime
    total_claimed: float
    total_claimable: float
    total_deductions: float
    employee_name: str | None = None
    has_review_flags: bool = False

    model_config = {"from_attributes": True}


class ClaimDetail(ClaimSummary):
    summary_json: dict | None
    reviewer_comment: str | None
    documents: list[ClaimDocumentOut] = []
    line_items: list[ClaimLineItemOut] = []
    extraction_fields: list[ExtractionFieldOut] = []


class ReviewAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|request_info)$")
    comment: str | None = None


class FeedbackCreate(BaseModel):
    feedback_type: str = Field(..., pattern="^(bug|feature)$")
    title: str
    description: str
    claim_id: UUID | None = None


class ValidationLineItem(BaseModel):
    category: str
    description: str
    amount_claimed: float
    amount_claimable: float
    limit_applied: float | None = None
    status_flag: str = "ok"
    deduction_comment: str | None = None
    review_required: bool = False


class ValidationResult(BaseModel):
    claim_type: str
    total_claimed: float
    total_claimable: float
    total_deductions: float
    line_items: list[ValidationLineItem]
    review_required: bool
    summary_json: dict
