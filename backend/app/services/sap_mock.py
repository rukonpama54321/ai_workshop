"""Mock SAP employee profile service for AI Workshop training."""

from dataclasses import dataclass

from app.models import EmployeeCategory


@dataclass
class EmployeeProfile:
    employee_id: str
    full_name: str
    job_group: str
    designation: str
    city_class: str
    employee_category: EmployeeCategory
    employment_status: str
    is_active: bool = True


MOCK_PROFILES: dict[str, EmployeeProfile] = {
    "employee_mgmt": EmployeeProfile(
        employee_id="10001234",
        full_name="Demo Management Employee",
        job_group="E",
        designation="Chief Manager",
        city_class="X",
        employee_category=EmployeeCategory.MANAGEMENT,
        employment_status="ACTIVE",
    ),
    "employee_workman": EmployeeProfile(
        employee_id="20005678",
        full_name="Demo Workman Employee",
        job_group="VII",
        designation="Senior Technician",
        city_class="Y",
        employee_category=EmployeeCategory.NON_MANAGEMENT,
        employment_status="ACTIVE",
    ),
    "employee_retired": EmployeeProfile(
        employee_id="20009999",
        full_name="Demo Retired Employee",
        job_group="IV",
        designation="Technician",
        city_class="Z",
        employee_category=EmployeeCategory.NON_MANAGEMENT,
        employment_status="RETIRED",
    ),
}


def get_employee_profile(username: str, employee_id: str | None = None) -> EmployeeProfile | None:
    if username in MOCK_PROFILES:
        return MOCK_PROFILES[username]
    if employee_id:
        for profile in MOCK_PROFILES.values():
            if profile.employee_id == employee_id:
                return profile
    return None
