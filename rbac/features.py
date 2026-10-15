"""
Application features: menu, URLs, and permission codenames are defined here.
Super admins only assign these permissions to roles in the UI; they are not edited in forms.
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


# Order in this list is the sidebar menu order.
APP_FEATURES: tuple[AppFeature, ...] = (
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
)

FEATURE_BY_CODENAME = {f.codename: f for f in APP_FEATURES}


def sync_permissions_to_database():
    """Create/update Permission rows from APP_FEATURES (run via seed_rbac on deploy)."""
    from rbac.models import Permission

    for feature in APP_FEATURES:
        Permission.objects.update_or_create(
            codename=feature.codename,
            defaults={"name": feature.name},
        )


def build_sidebar_items(allowed_codenames: set[str]) -> list[dict]:
    items = []
    for feature in APP_FEATURES:
        if not feature.show_in_menu or feature.codename not in allowed_codenames:
            continue
        try:
            url = reverse(feature.url_name)
        except NoReverseMatch:
            continue
        items.append(
            {
                "label": feature.menu_label,
                "url": url,
                "icon": feature.menu_icon,
                "codename": feature.codename,
            }
        )
    return items
