import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class ClaimStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VALIDATED = "validated"
    PENDING_REVIEW = "pending_review"
    PENDING_SIGNOFF = "pending_signoff"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


class EmployeeCategory(str, enum.Enum):
    MANAGEMENT = "management"
    NON_MANAGEMENT = "non_management"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.EMPLOYEE)
    employee_id: Mapped[str] = mapped_column(String(32), index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    job_group: Mapped[str] = mapped_column(String(16))
    designation: Mapped[str] = mapped_column(String(128), default="")
    city_class: Mapped[str] = mapped_column(String(1), default="Y")
    employee_category: Mapped[EmployeeCategory] = mapped_column(Enum(EmployeeCategory))
    employment_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claims: Mapped[list["Claim"]] = relationship(back_populates="user")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.UPLOADED, index=True)
    claim_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    submission_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_claimed: Mapped[float] = mapped_column(Float, default=0.0)
    total_claimable: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0)
    summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="claims", foreign_keys=[user_id])
    documents: Mapped[list["ClaimDocument"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    line_items: Mapped[list["ClaimLineItem"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    extraction_fields: Mapped[list["ExtractionField"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512))
    doc_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim: Mapped["Claim"] = relationship(back_populates="documents")


class ExtractionField(Base):
    __tablename__ = "extraction_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(128))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    method: Mapped[str] = mapped_column(String(64), default="unknown")
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)

    claim: Mapped["Claim"] = relationship(back_populates="extraction_fields")


class ClaimLineItem(Base):
    __tablename__ = "claim_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), index=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    amount_claimed: Mapped[float] = mapped_column(Float, default=0.0)
    amount_claimable: Mapped[float] = mapped_column(Float, default=0.0)
    limit_applied: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_flag: Mapped[str] = mapped_column(String(32), default="ok")
    deduction_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)

    claim: Mapped["Claim"] = relationship(back_populates="line_items")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(128), default="Guwahati")
    is_empaneled: Mapped[bool] = mapped_column(Boolean, default=True)


class HospitalDiscount(Base):
    __tablename__ = "hospital_discounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    discount_pct: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(String(255), default="synthetic")


class EligibilityLimit(Base):
    __tablename__ = "eligibility_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_category: Mapped[EmployeeCategory] = mapped_column(Enum(EmployeeCategory))
    job_group_min: Mapped[str | None] = mapped_column(String(16), nullable=True)
    job_group_max: Mapped[str | None] = mapped_column(String(16), nullable=True)
    city_class: Mapped[str] = mapped_column(String(8))
    limit_type: Mapped[str] = mapped_column(String(64))
    limit_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_actuals: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_reimbursable: Mapped[bool] = mapped_column(Boolean, default=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    claim_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("claims.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
