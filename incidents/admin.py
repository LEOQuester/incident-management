from django.contrib import admin

from incidents.models import Incident, IncidentPhoto, Notification, Authority, Category

admin.site.register(Authority)
admin.site.register(Category)


class IncidentPhotoInline(admin.TabularInline):
    model = IncidentPhoto
    extra = 0


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "status", "created_at")
    list_filter = ("status",)
    inlines = [IncidentPhotoInline]
    filter_horizontal = ("alerted_roles",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
