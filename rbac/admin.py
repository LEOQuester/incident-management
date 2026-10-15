from django.contrib import admin

from rbac.models import Permission, Role


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name")
    search_fields = ("codename", "name")
    readonly_fields = ("codename", "name")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_end_user_role")
    filter_horizontal = ("permissions",)
    search_fields = ("name",)
