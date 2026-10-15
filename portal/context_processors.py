from django.urls import reverse

from rbac.features import build_sidebar_items, FEATURE_BY_CODENAME


def navigation(request):
    if not request.user.is_authenticated:
        return {"sidebar_items": [], "admin_sidebar_items": []}

    user = request.user
    if user.is_superuser:
        allowed = set(FEATURE_BY_CODENAME.keys())
    else:
        allowed = user.get_permission_codenames()

    sidebar_items = build_sidebar_items(allowed)

    admin_sidebar_items = []
    if user.is_superuser:
        for url_name, label, icon in (
            ("portal:role_list", "Roles", "fa-users-cog"),
            ("portal:user_list", "Users", "fa-user-friends"),
        ):
            admin_sidebar_items.append(
                {"label": label, "url": reverse(url_name), "icon": icon}
            )

    return {
        "sidebar_items": sidebar_items,
        "admin_sidebar_items": admin_sidebar_items,
    }
