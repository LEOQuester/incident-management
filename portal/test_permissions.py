from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from rbac.models import Permission, Role


class PermissionListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_rbac", stdout=StringIO())
        cls.admin = User.objects.create_user(username="perm-admin", password="test-only")
        cls.admin.roles.add(Role.objects.get(name="System Administrator"))
        cls.custom = Permission.objects.create(
            codename="custom_test_perm",
            name="Custom Test Permission",
            is_builtin=False,
        )

    def test_list_shows_names(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("portal:permission_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "manage_cases")
        self.assertContains(response, "Review and Assign Cases")
        self.assertContains(response, "Custom Test Permission")
        self.assertContains(response, "perm-search-q")
        self.assertContains(response, "admin-permissions-list.js")

    def test_duplicate_builtin_codename_shows_validation_error(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("portal:permission_create"),
            {"codename": "manage_cases"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "built-in permission")
        self.assertEqual(
            Permission.objects.filter(codename="manage_cases").count(),
            1,
        )
