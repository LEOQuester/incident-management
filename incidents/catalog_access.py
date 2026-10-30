"""RBAC checks for authority/category catalog maintenance."""

KIND_PERMISSIONS = {
    "authorities": ("manage_authorities",),
    "categories": ("manage_categories",),
}


def user_can_manage_catalog(user, kind: str) -> bool:
    if not user.is_authenticated:
        return False
    codes = KIND_PERMISSIONS.get(kind, ())
    return any(user.has_rbac_permission(code) for code in codes)


def user_can_manage_any_catalog(user) -> bool:
    return user_can_manage_catalog(user, "authorities") or user_can_manage_catalog(
        user, "categories"
    )
