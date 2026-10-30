"""
Built-in features: codenames, URLs, and sidebar metadata synced to Permission rows.
Admins can create additional Permission rows in the portal UI.
"""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse


@dataclass(frozen=True)
class AppFeature:
    codename: str
    name: str
    url_name: str
    menu_label: str
    menu_icon: str = "fa-circle"
    show_in_menu: bool = True
    menu_section: str = "menu"  # "menu" | "admin"


# Order in this list is the sidebar menu order.
APP_FEATURES: tuple[AppFeature, ...] = (
    AppFeature("view_profile", "View Own Profile", "accounts:profile", "My Profile", "fa-user"),
    AppFeature(
        "manage_cases",
        "Review and Assign Cases",
        "portal:dashboard",
        "Cases & reports",
        "fa-list-check",
        show_in_menu=False,
    ),
    AppFeature(
        "view_allocated_cases",
        "View Unit-Assigned Cases",
        "portal:dashboard",
        "Cases & reports",
        "fa-list-check",
        show_in_menu=False,
    ),
    AppFeature(
        "update_allocated_cases",
        "Update Unit-Assigned Cases",
        "portal:dashboard",
        "Cases & reports",
        "fa-list-check",
        show_in_menu=False,
    ),
    AppFeature(
        "transfer_case",
        "Transfer Cases",
        "portal:dashboard",
        "Cases & reports",
        "fa-list-check",
        show_in_menu=False,
    ),
    AppFeature(
        "view_reports",
        "View Management Reports",
        "portal:dashboard",
        "Cases & reports",
        "fa-list-check",
        show_in_menu=False,
    ),
    AppFeature("manage_authorities", "Manage Authorities", "incidents:catalog_authorities", "Authorities", "fa-building", menu_section="admin"),
    AppFeature("manage_categories", "Manage Categories", "incidents:catalog_categories", "Categories", "fa-tags", menu_section="admin"),
    AppFeature(
        codename="view_dashboard",
        name="View Dashboard",
        url_name="portal:dashboard",
        menu_label="Dashboard",
        menu_icon="fa-home",
    ),
    AppFeature(
        codename="report_incident",
        name="Report Incident",
        url_name="incidents:report",
        menu_label="Report Incident",
        menu_icon="fa-triangle-exclamation",
    ),
    AppFeature(
        codename="view_permissions",
        name="View Permissions",
        url_name="portal:permission_list",
        menu_label="Permissions",
        menu_icon="fa-key",
        menu_section="admin",
    ),
    AppFeature(
        codename="manage_permissions",
        name="Manage Permissions",
        url_name="portal:permission_list",
        menu_label="Permissions",
        menu_icon="fa-key",
        menu_section="admin",
        show_in_menu=False,
    ),
    AppFeature(
        codename="manage_roles",
        name="Manage Roles",
        url_name="portal:role_list",
        menu_label="Roles",
        menu_icon="fa-users-cog",
        menu_section="admin",
    ),
    AppFeature(
        codename="manage_users",
        name="Manage Users",
        url_name="portal:user_list",
        menu_label="Users",
        menu_icon="fa-user-friends",
        menu_section="admin",
    ),
)

FEATURE_BY_CODENAME = {f.codename: f for f in APP_FEATURES}


def sync_permissions_to_database():
    """Create/update Permission rows from APP_FEATURES (run via seed_rbac on deploy)."""
    from rbac.models import Permission

    for index, feature in enumerate(APP_FEATURES):
        Permission.objects.update_or_create(
            codename=feature.codename,
            defaults={
                "name": feature.name,
                "is_builtin": True,
                "show_in_menu": feature.show_in_menu,
                "menu_label": feature.menu_label,
                "menu_icon": feature.menu_icon,
                "menu_section": feature.menu_section,
                "url_name": feature.url_name,
                "sort_order": index,
            },
        )


def build_sidebar_items(
    allowed_codenames: set[str],
    *,
    section: str = "menu",
) -> list[dict]:
    from rbac.models import Permission

    items = []
    permissions = Permission.objects.filter(
        show_in_menu=True,
        menu_section=section,
        codename__in=allowed_codenames,
    ).exclude(url_name="").order_by("sort_order", "name")
    seen_urls: set[str] = set()
    for perm in permissions:
        try:
            url = reverse(perm.url_name)
        except NoReverseMatch:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(
            {
                "label": perm.menu_label or perm.name,
                "url": url,
                "icon": perm.menu_icon or "fa-circle",
                "codename": perm.codename,
            }
        )
    return items
