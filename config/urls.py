from django.contrib import admin
<<<<<<< HEAD
=======
from django.conf.urls.static import static
from django.http import JsonResponse
>>>>>>> 68176b5 (Fix Railway deploy: ALLOWED_HOSTS, health check, start script)
from django.shortcuts import redirect
from django.urls import include, path


def health(request):
    """Lightweight health check for Railway / load balancers."""
    return JsonResponse({"status": "ok"})


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("portal:dashboard")
    return redirect("accounts:login")


urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("portal.urls")),
    path("home/", root_redirect, name="home"),
]
