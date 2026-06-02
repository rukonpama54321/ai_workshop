import pytest
from datetime import date

from app.models import EmployeeCategory
from app.pipeline.claim_validator import ExtractedClaimData, validate_claim


class FakeUser:
    def __init__(self, category, job_group, city_class):
        self.employee_category = category
        self.job_group = job_group
        self.city_class = city_class


class FakeLimit:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def non_mgmt_limits():
    return [
        FakeLimit(
            employee_category=EmployeeCategory.NON_MANAGEMENT,
            job_group_min=None,
            job_group_max=None,
            city_class="X",
            limit_type="cabin_per_day",
            limit_amount=4500,
            is_actuals=False,
        ),
        FakeLimit(
            employee_category=EmployeeCategory.NON_MANAGEMENT,
            job_group_min=None,
            job_group_max=None,
            city_class="YZ",
            limit_type="cabin_per_day",
            limit_amount=3555,
            is_actuals=False,
        ),
    ]


def test_cabin_cap_non_management(non_mgmt_limits):
    user = FakeUser(EmployeeCategory.NON_MANAGEMENT, "VII", "X")
    extracted = ExtractedClaimData(
        claim_type="inpatient",
        hospital_name="GNRC Hospitals",
        invoice_date=date(2026, 5, 1),
        prescription_date=None,
        discharge_date=date(2026, 5, 10),
        room_charge_per_day=6000,
        room_days=2,
        discount_claimed_pct=8.5,
        line_items=[],
        medicines=[],
        diagnosis="Fever",
        low_confidence_fields=[],
    )
    result = validate_claim(
        user=user,
        extracted=extracted,
        submission_date=date(2026, 6, 1),
        eligibility_limits=non_mgmt_limits,
        hospital_discounts={"GNRC Hospitals": 8.5},
        reimbursable_medicines={"paracetamol"},
        non_reimbursable_medicines=set(),
    )
    cabin = next(i for i in result.line_items if i.category == "cabin")
    assert cabin.amount_claimed == 12000
    assert cabin.amount_claimable == 9000
    assert cabin.deduction_comment is not None


def test_non_reimbursable_medicine(non_mgmt_limits):
    user = FakeUser(EmployeeCategory.NON_MANAGEMENT, "VII", "Y")
    extracted = ExtractedClaimData(
        claim_type="outpatient",
        hospital_name=None,
        invoice_date=date(2026, 5, 1),
        prescription_date=None,
        discharge_date=None,
        room_charge_per_day=None,
        room_days=None,
        discount_claimed_pct=None,
        line_items=[],
        medicines=[{"name": "sugar testing kit", "amount": 500}],
        diagnosis=None,
        low_confidence_fields=[],
    )
    result = validate_claim(
        user=user,
        extracted=extracted,
        submission_date=date(2026, 6, 1),
        eligibility_limits=non_mgmt_limits,
        hospital_discounts={},
        reimbursable_medicines={"paracetamol"},
        non_reimbursable_medicines={"sugar testing kit"},
    )
    med = next(i for i in result.line_items if i.category == "medicine")
    assert med.amount_claimable == 0
    assert med.status_flag == "non_reimbursable"
