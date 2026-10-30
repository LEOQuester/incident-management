from django.urls import path

from incidents import views
from incidents import views_assignment

app_name = "incidents"

urlpatterns = [
    path("queue/", views.case_queue, name="queue"),
    path("<int:pk>/edit/", views.edit_own_incident, name="edit"),
    path("<int:pk>/update/", views.case_update, name="update"),
    path("<int:pk>/assign/options/", views_assignment.case_assign_wizard_options, name="assign_options"),
    path("<int:pk>/assign/", views_assignment.case_assign_wizard_submit, name="assign_submit"),
    path("attachments/<int:pk>/", views.attachment_download, name="attachment"),
    path("attachments/<int:pk>/preview/", views.attachment_preview, name="attachment_preview"),
    path("photos/<int:pk>/", views.attachment_download, {"legacy": True}, name="photo"),
    path("photos/<int:pk>/preview/", views.attachment_preview, {"legacy": True}, name="photo_preview"),
    path("catalogs/", views.catalog_home, name="catalog_home"),
    path(
        "catalog/authorities/",
        views.catalog_list,
        {"kind": "authorities"},
        name="catalog_authorities",
    ),
    path(
        "catalog/categories/",
        views.catalog_list,
        {"kind": "categories"},
        name="catalog_categories",
    ),
    path("catalog/<str:kind>/", views.catalog_list, name="catalog"),
    path("catalog/<str:kind>/new/", views.catalog_create, name="catalog_create"),
    path("catalog/<str:kind>/<int:pk>/edit/", views.catalog_edit, name="catalog_edit"),
    path("catalog/<str:kind>/<int:pk>/delete/", views.catalog_delete, name="catalog_delete"),
    path("<int:pk>/", views.incident_detail, name="detail"),
    path("report/", views.report_incident, name="report"),
    path("notifications/", views.notifications_list, name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
]
