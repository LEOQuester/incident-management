from django.test import TestCase

from accounts.models import User
from django.urls import reverse


class PermissionRedirectTests(TestCase):
    def test_user_without_dashboard_permission_is_not_redirected_in_a_loop(self):
        user = User.objects.create_user(username="no-access", password="test-password-123")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:dashboard"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], reverse("portal:access_denied"))

# Create your tests here.
