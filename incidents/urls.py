from django.urls import path

from incidents import views

app_name = "incidents"

urlpatterns = [
    path("queue/", views.case_queue, name="queue"),
    path("<int:pk>/update/", views.case_update, name="update"),
    path("attachments/<int:pk>/", views.attachment_download, name="attachment"),
    path("photos/<int:pk>/", views.attachment_download, {"legacy": True}, name="photo"),
    path("catalog/<str:kind>/", views.catalog, name="catalog"),
    path("catalog/<str:kind>/<int:pk>/", views.catalog, name="catalog_edit"),
    path("catalogs/", views.catalog_home, name="catalog_home"),
    path("<int:pk>/", views.incident_detail, name="detail"),
    path("report/", views.report_incident, name="report"),
    path("notifications/", views.notifications_list, name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
]
