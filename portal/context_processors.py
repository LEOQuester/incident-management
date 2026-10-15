from django.urls import NoReverseMatch, reverse

from rbac.models import Permission


def navigation(request):
    if not request.user.is_authenticated:
        return {"sidebar_items": [], "admin_sidebar_items": []}

    user = request.user
    if user.is_superuser:
        perms = Permission.objects.exclude(url_name="").order_by("name")
    else:
        perms = (
            Permission.objects.filter(roles__users=user)
            .exclude(url_name="")
            .distinct()
            .order_by("name")
        )

    sidebar_items = []
    for perm in perms:
        try:
            url = reverse(perm.url_name)
        except NoReverseMatch:
            continue
        sidebar_items.append(
            {
                "label": perm.sidebar_label,
                "url": url,
                "icon": perm.menu_icon or "fa-circle",
                "codename": perm.codename,
            }
        )

    admin_sidebar_items = []
    if user.is_superuser:
        admin_links = [
            ("portal:permission_list", "Permissions", "fa-key"),
            ("portal:role_list", "Roles", "fa-users-cog"),
            ("portal:user_list", "Users", "fa-user-friends"),
        ]
        for url_name, label, icon in admin_links:
            admin_sidebar_items.append(
                {"label": label, "url": reverse(url_name), "icon": icon}
            )

    return {
        "sidebar_items": sidebar_items,
        "admin_sidebar_items": admin_sidebar_items,
    }
