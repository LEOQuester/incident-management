from django.urls import path

from portal import views

app_name = "portal"

# Use "manage/" not "admin/" — Django's /admin/ is reserved for django.contrib.admin
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("manage/permissions/", views.permission_list, name="permission_list"),
    path("manage/permissions/new/", views.permission_create, name="permission_create"),
    path(
        "manage/permissions/<int:pk>/edit/",
        views.permission_edit,
        name="permission_edit",
    ),
    path(
        "manage/permissions/<int:pk>/delete/",
        views.permission_delete,
        name="permission_delete",
    ),
    path("manage/roles/", views.role_list, name="role_list"),
    path("manage/roles/new/", views.role_create, name="role_create"),
    path("manage/roles/<int:pk>/edit/", views.role_edit, name="role_edit"),
    path("manage/roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("manage/users/", views.user_list, name="user_list"),
    path("manage/users/new/", views.user_create, name="user_create"),
    path("manage/users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("manage/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
