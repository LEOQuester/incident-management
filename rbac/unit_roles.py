"""Helpers for authority-unit staff roles."""

from incidents.models import Authority
from rbac.models import Permission, Role

UNIT_STAFF_PERMISSIONS = (
    "view_profile",
    "view_dashboard",
    "view_allocated_cases",
    "update_allocated_cases",
    "transfer_case",
)


def unit_staff_role_name(authority: Authority) -> str:
    return f"{authority.name} staff"


def ensure_unit_staff_role(authority: Authority) -> Role:
    role, _ = Role.objects.update_or_create(
        name=unit_staff_role_name(authority),
        defaults={
            "authority": authority,
            "is_end_user_role": False,
            "description": f"Handle cases assigned to {authority.name}.",
        },
    )
    perms = Permission.objects.filter(codename__in=UNIT_STAFF_PERMISSIONS)
    role.permissions.set(perms)
    return role
