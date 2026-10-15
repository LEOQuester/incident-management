from django.contrib import admin

from rbac.models import Permission, Role


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "url_name")
    search_fields = ("codename", "name", "url_name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    filter_horizontal = ("permissions",)
    search_fields = ("name",)
