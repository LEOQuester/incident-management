"""Default route after login or visiting site root while authenticated."""

from django.urls import reverse


def get_post_login_url(user) -> str:
    if not user.is_authenticated:
        return reverse("accounts:login")
    if user.has_rbac_permission("report_incident"):
        return reverse("incidents:report")
    if user.has_rbac_permission("view_dashboard"):
        return reverse("portal:dashboard")
    return reverse("portal:access_denied")
