from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path


def health(request):
    """Lightweight health check for Railway / load balancers."""
    return JsonResponse({"status": "ok"})


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("portal:dashboard")
    return redirect("accounts:login")


def legacy_superadmin_redirect(request, resource, trail=""):
    """Old /admin/{permissions|roles|users}/… URLs → /manage/… (before django.contrib.admin)."""
    base = f"/manage/{resource}/"
    target = f"{base}{trail}" if trail else base
    return redirect(target)


urlpatterns = [
    path("health/", health, name="health"),
    # Legacy super-admin paths (must be registered before django.contrib.admin /admin/)
    path(
        "admin/permissions/",
        lambda r: redirect("portal:permission_list"),
        name="legacy_permissions",
    ),
    path(
        "admin/permissions/<path:trail>",
        lambda r, trail: redirect("portal:permission_list"),
    ),
    path(
        "admin/roles/",
        legacy_superadmin_redirect,
        {"resource": "roles"},
        name="legacy_roles",
    ),
    path(
        "admin/roles/<path:trail>",
        legacy_superadmin_redirect,
        {"resource": "roles"},
    ),
    path(
        "admin/users/",
        legacy_superadmin_redirect,
        {"resource": "users"},
        name="legacy_users",
    ),
    path(
        "admin/users/<path:trail>",
        legacy_superadmin_redirect,
        {"resource": "users"},
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("incidents/", include("incidents.urls")),
    path("", include("portal.urls")),
    path("home/", root_redirect, name="home"),
]

# Evidence is served only by authenticated incidents attachment endpoints.
