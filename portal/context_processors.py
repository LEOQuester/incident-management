from rbac.features import FEATURE_BY_CODENAME, build_sidebar_items


def navigation(request):
    if not request.user.is_authenticated:
        return {"sidebar_items": [], "admin_sidebar_items": []}

    user = request.user
    if user.is_superuser:
        allowed = set(FEATURE_BY_CODENAME.keys())
    else:
        allowed = user.get_permission_codenames()

    return {
        "sidebar_items": build_sidebar_items(allowed, section="menu"),
        "admin_sidebar_items": build_sidebar_items(allowed, section="admin"),
    }
