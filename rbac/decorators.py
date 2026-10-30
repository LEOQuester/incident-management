from functools import wraps

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def permission_required(codename: str):
    """Require logged-in user to hold an RBAC permission via assigned roles."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            user = request.user
            if not user.is_authenticated:
                return redirect("accounts:login")
            if user.has_rbac_permission(codename):
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                "You do not have permission to access this page.",
            )
            return redirect("portal:access_denied")

        return _wrapped

    return decorator


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.is_superuser:
            messages.error(request, "Superuser access is required.")
            return redirect("portal:access_denied")
        return view_func(request, *args, **kwargs)

    return _wrapped
