from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("FMSC", {"fields": ("phone", "mc_number", "cpm_number", "roles")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("FMSC", {"fields": ("phone",)}),
    )
    list_display = (
        "username",
        "email",
        "phone",
        "mc_number",
        "cpm_number",
        "is_superuser",
        "is_active",
    )
    filter_horizontal = ("roles", "groups", "user_permissions")
