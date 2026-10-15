from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from rbac.decorators import permission_required, superuser_required
from rbac.forms import PermissionForm, RoleForm
from accounts.forms import AdminUserForm
from accounts.models import User
from rbac.models import Permission, Role


@login_required
@permission_required("view_dashboard")
def dashboard(request):
    return render(
        request,
        "portal/dashboard.html",
        {"page_title": "Dashboard"},
    )


@superuser_required
def permission_list(request):
    permissions = Permission.objects.all()
    return render(
        request,
        "portal/admin/permission_list.html",
        {"permissions": permissions, "page_title": "Permissions"},
    )


@superuser_required
def permission_create(request):
    form = PermissionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:permission_list")
    return render(
        request,
        "portal/admin/permission_form.html",
        {"form": form, "page_title": "Create Permission"},
    )


@superuser_required
def permission_edit(request, pk):
    perm = Permission.objects.get(pk=pk)
    form = PermissionForm(request.POST or None, instance=perm)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:permission_list")
    return render(
        request,
        "portal/admin/permission_form.html",
        {"form": form, "page_title": "Edit Permission", "object": perm},
    )


@superuser_required
def permission_delete(request, pk):
    perm = Permission.objects.get(pk=pk)
    if request.method == "POST":
        perm.delete()
        return redirect("portal:permission_list")
    return render(
        request,
        "portal/admin/confirm_delete.html",
        {
            "object": perm,
            "page_title": "Delete Permission",
            "cancel_url": "portal:permission_list",
        },
    )


@superuser_required
def role_list(request):
    roles = Role.objects.prefetch_related("permissions")
    return render(
        request,
        "portal/admin/role_list.html",
        {"roles": roles, "page_title": "Roles"},
    )


@superuser_required
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


@superuser_required
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


@superuser_required
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


@superuser_required
def user_list(request):
    users = User.objects.prefetch_related("roles")
    return render(
        request,
        "portal/admin/user_list.html",
        {"users": users, "page_title": "Users"},
    )


@superuser_required
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


@superuser_required
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


@superuser_required
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
