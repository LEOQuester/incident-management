"""
Default authorities, roles, categories, and bootstrap admin for seed_rbac.

Run anywhere: python manage.py seed_rbac
"""

from dataclasses import dataclass

from rbac.features import APP_FEATURES

SYSTEM_ADMINISTRATOR_PERMISSIONS = tuple(f.codename for f in APP_FEATURES)

UNIT_HEAD_PERMISSIONS = (
    "view_profile",
    "view_dashboard",
    "view_allocated_cases",
    "update_allocated_cases",
    "transfer_case",
)

END_USER_PERMISSIONS = (
    "view_profile",
    "view_dashboard",
    "report_incident",
)

DEFAULT_SUPERUSER = {
    "username": "Lakindu",
    "email": "induwaralakindu09@gmail.com",
    "password": "Lakindu123!@",
}


@dataclass(frozen=True)
class AuthoritySeed:
    name: str
    role_name: str
    permission_codenames: tuple[str, ...]
    role_description: str
    use_system_administrator_role: bool = False


SEED_AUTHORITIES: tuple[AuthoritySeed, ...] = (
    AuthoritySeed(
        name="Developers",
        role_name="System Administrator",
        permission_codenames=SYSTEM_ADMINISTRATOR_PERMISSIONS,
        role_description="Full portal administration and catalog maintenance.",
        use_system_administrator_role=True,
    ),
    AuthoritySeed(
        name="IT Department",
        role_name="Department Head",
        permission_codenames=UNIT_HEAD_PERMISSIONS,
        role_description="Lead IT Department case handling on the dashboard.",
    ),
    AuthoritySeed(
        name="Maintenance and cleaning",
        role_name="Cleaning Head",
        permission_codenames=UNIT_HEAD_PERMISSIONS,
        role_description="Lead maintenance and cleaning case handling.",
    ),
    AuthoritySeed(
        name="Security",
        role_name="Admin Security Officer",
        permission_codenames=UNIT_HEAD_PERMISSIONS,
        role_description="Lead security-related case handling.",
    ),
)

SEED_AUTHORITY_NAMES = frozenset(a.name for a in SEED_AUTHORITIES)

GLOBAL_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Student": END_USER_PERMISSIONS,
    "Lecturer": END_USER_PERMISSIONS,
    "System Administrator": SYSTEM_ADMINISTRATOR_PERMISSIONS,
}

END_USER_ROLE_NAMES = frozenset({"Student", "Lecturer"})

DEFAULT_CATEGORIES = (
    "Classroom",
    "IT",
    "Maintenance",
    "Examination",
    "Other",
)

# Roles and legacy unit staff names removed on each seed run.
RETIRED_ROLE_NAMES = (
    "Member",
    "Administrator",
    "Security",
    "IT Support",
    "Student Affairs",
    "Relevant Authority",
    "Faculty Management",
)
