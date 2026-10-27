from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.forms import AdminUserForm
from accounts.models import User
from rbac.decorators import permission_required
from rbac.features import sync_permissions_to_database
from rbac.forms import PermissionCreateForm, RoleForm, display_name_for_codename
from rbac.portal_access import can_manage_permissions, can_view_permissions
from portal.dashboard import dashboard_context
from rbac.models import Permission, Role


@login_required
def access_denied(request):
    """A stable destination for authenticated users without portal access."""
    return render(request, "portal/access_denied.html", {"page_title": "Access denied"})


@login_required
@permission_required("view_dashboard")
def dashboard(request):
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
    permissions = Permission.objects.all().order_by("sort_order", "name")
    return render(
        request,
        "portal/admin/permission_list.html",
        {
            "permissions": permissions,
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
    roles = Role.objects.prefetch_related("permissions")
    return render(
        request,
        "portal/admin/role_list.html",
        {"roles": roles, "page_title": "Roles"},
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
    users = User.objects.prefetch_related("roles")
    return render(
        request,
        "portal/admin/user_list.html",
        {"users": users, "page_title": "Users"},
    )


@permission_required("manage_users")
def user_create(request):
    form = AdminUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get("password")
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        form.save_m2m()
        return redirect("portal:user_list")
    return render(
        request,
        "portal/admin/user_form.html",
        {"form": form, "page_title": "Create User"},
    )


@permission_required("manage_users")
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    form = AdminUserForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:user_list")
    return render(
        request,
        "portal/admin/user_form.html",
        {"form": form, "page_title": "Edit User", "object": user},
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
