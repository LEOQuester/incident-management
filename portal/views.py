from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.forms import AdminUserForm
from accounts.models import User
from rbac.decorators import permission_required
from rbac.features import sync_permissions_to_database
from rbac.forms import PermissionCreateForm, RoleForm, display_name_for_codename
from rbac.portal_access import can_manage_permissions, can_view_permissions
from incidents.access import QUEUE_ACCESS_CODENAMES
from portal.dashboard import dashboard_context
from portal.pagination import ADMIN_PAGE_SIZE, paginate
from rbac.models import Permission, Role


@login_required
def access_denied(request):
    """A stable destination for authenticated users without portal access."""
    return render(request, "portal/access_denied.html", {"page_title": "Access denied"})


@login_required
def dashboard(request):
    capabilities = request.user.get_permission_codenames()
    if "view_dashboard" not in capabilities and not (
        capabilities & set(QUEUE_ACCESS_CODENAMES)
    ):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("portal:access_denied")
    context = dashboard_context(request)
    if not isinstance(context, dict):
        return context
    return render(request, "portal/dashboard.html", context)


@login_required
def permission_list(request):
    if not can_view_permissions(request.user):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("portal:access_denied")
    sync_permissions_to_database()
    permissions = list(
        Permission.objects.all().order_by("sort_order", "name")
    )
    return render(
        request,
        "portal/admin/permission_list.html",
        {
            "permissions": permissions,
            "permission_count": len(permissions),
            "page_title": "Permissions",
            "can_manage_permissions": can_manage_permissions(request.user),
        },
    )


@permission_required("manage_permissions")
def permission_create(request):
    form = PermissionCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        codename = form.cleaned_data["codename"]
        Permission.objects.create(
            codename=codename,
            name=display_name_for_codename(codename),
            is_builtin=False,
        )
        messages.success(request, "Permission created.")
        return redirect("portal:permission_list")
    return render(
        request,
        "portal/admin/permission_form.html",
        {"form": form, "page_title": "Create Permission"},
    )


@permission_required("manage_permissions")
def permission_delete(request, pk):
    permission = Permission.objects.get(pk=pk)
    if permission.is_builtin:
        messages.error(request, "Built-in permissions cannot be deleted.")
        return redirect("portal:permission_list")
    if request.method == "POST":
        permission.delete()
        messages.success(request, "Permission deleted.")
        return redirect("portal:permission_list")
    return render(
        request,
        "portal/admin/confirm_delete.html",
        {
            "object": permission,
            "page_title": "Delete Permission",
            "cancel_url": "portal:permission_list",
        },
    )


@permission_required("manage_roles")
def role_list(request):
    page_obj, previous_url, next_url = paginate(
        request,
        Role.objects.select_related("authority")
        .prefetch_related("permissions")
        .order_by("name"),
        per_page=ADMIN_PAGE_SIZE,
    )
    return render(
        request,
        "portal/admin/role_list.html",
        {
            "page_obj": page_obj,
            "previous_url": previous_url,
            "next_url": next_url,
            "page_title": "Roles",
        },
    )


@permission_required("manage_roles")
def role_create(request):
    form = RoleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:role_list")
    return render(
        request,
        "portal/admin/role_form.html",
        {"form": form, "page_title": "Create Role"},
    )


@permission_required("manage_roles")
def role_edit(request, pk):
    role = Role.objects.get(pk=pk)
    form = RoleForm(request.POST or None, instance=role)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:role_list")
    return render(
        request,
        "portal/admin/role_form.html",
        {"form": form, "page_title": "Edit Role", "object": role},
    )


@permission_required("manage_roles")
def role_delete(request, pk):
    role = Role.objects.get(pk=pk)
    if request.method == "POST":
        role.delete()
        return redirect("portal:role_list")
    return render(
        request,
        "portal/admin/confirm_delete.html",
        {
            "object": role,
            "page_title": "Delete Role",
            "cancel_url": "portal:role_list",
        },
    )


@permission_required("manage_users")
def user_list(request):
    page_obj, previous_url, next_url = paginate(
        request,
        User.objects.prefetch_related("roles", "roles__authority").order_by(
            "username"
        ),
        per_page=ADMIN_PAGE_SIZE,
    )
    return render(
        request,
        "portal/admin/user_list.html",
        {
            "page_obj": page_obj,
            "previous_url": previous_url,
            "next_url": next_url,
            "page_title": "Users",
        },
    )


@permission_required("manage_users")
def user_create(request):
    form = AdminUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User created.")
        return redirect("portal:user_list")
    return render(
        request,
        "portal/admin/user_form.html",
        {"form": form, "page_title": "New user", "is_create": True},
    )


@permission_required("manage_users")
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    form = AdminUserForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User updated.")
        return redirect("portal:user_list")
    return render(
        request,
        "portal/admin/user_form.html",
        {
            "form": form,
            "page_title": "Edit user",
            "object": user,
            "is_create": False,
        },
    )


@permission_required("manage_users")
def user_delete(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == "POST":
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect("portal:user_list")
        user.delete()
        return redirect("portal:user_list")
    return render(
        request,
        "portal/admin/confirm_delete.html",
        {
            "object": user,
            "page_title": "Delete User",
            "cancel_url": "portal:user_list",
        },
    )
