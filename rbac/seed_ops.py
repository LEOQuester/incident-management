"""Database operations invoked by seed_rbac."""

from django.contrib.auth import get_user_model

from incidents.models import Authority, Incident
from rbac.models import Permission, Role
from rbac.seed_catalog import (
    DEFAULT_SUPERUSER,
    GLOBAL_ROLE_PERMISSIONS,
    RETIRED_ROLE_NAMES,
    SEED_AUTHORITIES,
    SEED_AUTHORITY_NAMES,
    END_USER_ROLE_NAMES,
)
from rbac.superuser_access import SYSTEM_ADMIN_ROLE_NAME, assign_system_administrator_role


def role_description(name: str) -> str:
    for entry in SEED_AUTHORITIES:
        if entry.role_name == name or (entry.use_system_administrator_role and name == SYSTEM_ADMIN_ROLE_NAME):
            return entry.role_description
    descriptions = {
        "Student": "Submit and manage own incidents; profile access.",
        "Lecturer": "Submit and manage own incidents; profile access.",
    }
    return descriptions.get(name, "")


def sync_global_roles() -> None:
    for name, codenames in GLOBAL_ROLE_PERMISSIONS.items():
        role, _ = Role.objects.update_or_create(
            name=name,
            defaults={
                "description": role_description(name),
                "is_end_user_role": name in END_USER_ROLE_NAMES,
            },
        )
        role.permissions.set(Permission.objects.filter(codename__in=codenames))


def sync_authorities_and_unit_roles() -> None:
    for entry in SEED_AUTHORITIES:
        authority, _ = Authority.objects.get_or_create(
            name=entry.name,
            defaults={"is_active": True},
        )
        if not authority.is_active:
            authority.is_active = True
            authority.save(update_fields=["is_active"])

        if entry.use_system_administrator_role:
            role = Role.objects.filter(name=SYSTEM_ADMIN_ROLE_NAME).first()
            if role is None:
                continue
            role.authority = authority
            role.description = entry.role_description
            role.is_end_user_role = False
            role.save(update_fields=["authority", "description", "is_end_user_role"])
            role.permissions.set(
                Permission.objects.filter(codename__in=entry.permission_codenames)
            )
            continue

        role, _ = Role.objects.update_or_create(
            name=entry.role_name,
            defaults={
                "authority": authority,
                "is_end_user_role": False,
                "description": entry.role_description,
            },
        )
        if role.authority_id != authority.pk:
            role.authority = authority
            role.save(update_fields=["authority"])
        role.permissions.set(
            Permission.objects.filter(codename__in=entry.permission_codenames)
        )


def purge_non_seed_authorities() -> int:
    """Remove authorities not in the seed catalog (cases unassigned first)."""
    stale = Authority.objects.exclude(name__in=SEED_AUTHORITY_NAMES)
    stale_ids = list(stale.values_list("pk", flat=True))
    if not stale_ids:
        return 0
    Incident.objects.filter(authority_id__in=stale_ids).update(authority=None)
    deleted, _ = stale.delete()
    return deleted


def delete_retired_roles() -> int:
    staff_deleted, _ = Role.objects.filter(name__endswith=" staff").delete()
    named_deleted, _ = Role.objects.filter(name__in=RETIRED_ROLE_NAMES).delete()
    return staff_deleted + named_deleted


def ensure_bootstrap_superuser() -> tuple[bool, str]:
    """Create or update the default Lakindu system admin. Returns (created, username)."""
    cfg = DEFAULT_SUPERUSER
    User = get_user_model()
    user = User.objects.filter(username=cfg["username"]).first()
    if user is None:
        user = User.objects.filter(email__iexact=cfg["email"]).first()
    created = user is None
    if created:
        user = User(username=cfg["username"])
    user.username = cfg["username"]
    user.email = cfg["email"]
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(cfg["password"])
    user.save()
    assign_system_administrator_role(user)
    return created, cfg["username"]
