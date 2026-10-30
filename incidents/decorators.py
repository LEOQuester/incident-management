from functools import wraps

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect

from incidents.catalog_access import user_can_manage_catalog


def catalog_permission_required(view_func):
    """Require catalog access for the URL kind (authorities | categories)."""

    @wraps(view_func)
    def wrapped(request: HttpRequest, kind: str, *args, **kwargs) -> HttpResponse:
        if kind not in {"authorities", "categories"}:
            raise Http404
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not user_can_manage_catalog(request.user, kind):
            messages.error(request, "You do not have permission to access this page.")
            return redirect("portal:access_denied")
        return view_func(request, kind, *args, **kwargs)

    return wrapped
