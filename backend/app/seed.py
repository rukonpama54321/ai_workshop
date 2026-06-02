"""Seed demo users and master data for workshop."""

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import (
    EligibilityLimit,
    EmployeeCategory,
    Hospital,
    HospitalDiscount,
    Medicine,
    User,
    UserRole,
)
from app.services.sap_mock import MOCK_PROFILES


def seed_users(db: Session) -> None:
    demos = [
        ("employee_mgmt", "demo123", UserRole.EMPLOYEE, "employee_mgmt"),
        ("employee_workman", "demo123", UserRole.EMPLOYEE, "employee_workman"),
        ("employee_retired", "demo123", UserRole.EMPLOYEE, "employee_retired"),
        ("reviewer", "demo123", UserRole.REVIEWER, "employee_mgmt"),
        ("admin", "demo123", UserRole.ADMIN, "employee_mgmt"),
    ]
    for username, password, role, profile_key in demos:
        if db.query(User).filter(User.username == username).first():
            continue
        profile = MOCK_PROFILES[profile_key]
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                employee_id=profile.employee_id,
                full_name=profile.full_name,
                job_group=profile.job_group,
                designation=profile.designation,
                city_class=profile.city_class,
                employee_category=profile.employee_category,
                employment_status=profile.employment_status,
            )
        )
    db.commit()


def seed_eligibility_limits(db: Session) -> None:
    if db.query(EligibilityLimit).count():
        return

    rows = [
        # Non-management cabin (Table 16)
        (EmployeeCategory.NON_MANAGEMENT, None, None, "X", "cabin_per_day", 4500, False, "Non-mgmt X class"),
        (EmployeeCategory.NON_MANAGEMENT, None, None, "YZ", "cabin_per_day", 3555, False, "Non-mgmt Y/Z class"),
        # Management JG 02-F (Table 11)
        (EmployeeCategory.MANAGEMENT, "02", "F", "X", "cabin_per_day", 8500, False, "Mgmt JG 02-F X"),
        (EmployeeCategory.MANAGEMENT, "02", "F", "YZ", "cabin_per_day", 7650, False, "Mgmt JG 02-F YZ"),
        # Management JG G+ actuals
        (EmployeeCategory.MANAGEMENT, "G", None, "X", "cabin_per_day", None, True, "Mgmt JG G+ actuals"),
        (EmployeeCategory.MANAGEMENT, "G", None, "YZ", "cabin_per_day", None, True, "Mgmt JG G+ actuals YZ"),
    ]
    for cat, jg_min, jg_max, city, ltype, amount, actuals, notes in rows:
        db.add(
            EligibilityLimit(
                employee_category=cat,
                job_group_min=jg_min,
                job_group_max=jg_max,
                city_class=city,
                limit_type=ltype,
                limit_amount=amount,
                is_actuals=actuals,
                notes=notes,
            )
        )
    db.commit()


def seed_hospitals_and_discounts(db: Session) -> None:
    if db.query(Hospital).count():
        return

    synthetic = [
        ("Apollo Hospitals Guwahati", "Guwahati", 10.0),
        ("GNRC Hospitals", "Guwahati", 8.5),
        ("Excel Care Hospital", "Guwahati", 12.0),
        ("Down Town Hospital", "Guwahati", 7.5),
        ("Narayana Superspeciality Hospital", "Guwahati", 9.0),
        ("Sanjevani Hospital", "Bokakhat", 6.5),
        ("Assam Medical College Hospital", "Dibrugarh", 5.0),
    ]
    for name, city, pct in synthetic:
        h = Hospital(name=name, city=city, is_empaneled=True)
        db.add(h)
        db.flush()
        db.add(HospitalDiscount(hospital_id=h.id, discount_pct=pct, notes="synthetic workshop seed"))
    db.commit()


def seed_medicines(db: Session) -> None:
    if db.query(Medicine).count():
        return

    reimbursable = ["paracetamol", "amoxicillin", "metformin", "azithromycin", "crocin", "p500", "omeprazole"]
    blocked = ["sugar testing kit", "vitamin supplement premium", "cosmetic cream"]

    for name in reimbursable:
        db.add(Medicine(name=name, is_reimbursable=True))
    for name in blocked:
        db.add(Medicine(name=name, is_reimbursable=False))
    db.commit()


def run_all_seeds(db: Session) -> None:
    seed_users(db)
    seed_eligibility_limits(db)
    seed_hospitals_and_discounts(db)
    seed_medicines(db)
