from django.urls import path

from portal import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("admin/permissions/", views.permission_list, name="permission_list"),
    path("admin/permissions/new/", views.permission_create, name="permission_create"),
    path("admin/permissions/<int:pk>/edit/", views.permission_edit, name="permission_edit"),
    path(
        "admin/permissions/<int:pk>/delete/",
        views.permission_delete,
        name="permission_delete",
    ),
    path("admin/roles/", views.role_list, name="role_list"),
    path("admin/roles/new/", views.role_create, name="role_create"),
    path("admin/roles/<int:pk>/edit/", views.role_edit, name="role_edit"),
    path("admin/roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("admin/users/", views.user_list, name="user_list"),
    path("admin/users/new/", views.user_create, name="user_create"),
    path("admin/users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("admin/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
