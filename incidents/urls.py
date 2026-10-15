from django.urls import path

from incidents import views

app_name = "incidents"

urlpatterns = [
    path("report/", views.report_incident, name="report"),
    path("notifications/", views.notifications_list, name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
]
