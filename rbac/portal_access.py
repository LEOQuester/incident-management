from django.contrib.auth.models import AbstractBaseUser


def can_view_permissions(user: AbstractBaseUser) -> bool:
    if not user.is_authenticated:
        return False
    return user.has_rbac_permission("view_permissions") or user.has_rbac_permission(
        "manage_permissions"
    )


def can_manage_permissions(user: AbstractBaseUser) -> bool:
    if not user.is_authenticated:
        return False
    return user.has_rbac_permission("manage_permissions")
