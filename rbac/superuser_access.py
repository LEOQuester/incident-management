"""Grant portal RBAC roles to Django superusers (app access is role-based, not is_superuser)."""

from django.contrib.auth import get_user_model

from rbac.models import Role

SYSTEM_ADMIN_ROLE_NAME = "System Administrator"

PORTAL_ADMIN_CODENAMES = (
    "manage_users",
    "manage_roles",
    "manage_permissions",
    "view_permissions",
)


def assign_system_administrator_role(user) -> bool:
    """Attach System Administrator role (full APP_FEATURES permissions)."""
    if not getattr(user, "is_authenticated", True) or user.pk is None:
        return False
    role = Role.objects.filter(name=SYSTEM_ADMIN_ROLE_NAME).first()
    if not role:
        return False
    user.roles.add(role)
    return True


def sync_superuser_portal_roles() -> int:
    """Ensure every active superuser has the System Administrator role. Returns count newly linked."""
    role = Role.objects.filter(name=SYSTEM_ADMIN_ROLE_NAME).first()
    if not role:
        return 0
    User = get_user_model()
    linked = 0
    for user in User.objects.filter(is_superuser=True, is_active=True):
        if not user.roles.filter(pk=role.pk).exists():
            user.roles.add(role)
            linked += 1
    return linked
