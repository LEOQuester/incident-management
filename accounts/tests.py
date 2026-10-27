from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from rbac.models import Role


class CSRFFormTests(TestCase):
    def test_login_form_is_not_cached_and_accepts_its_current_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("accounts:login")

        response = client.get(login_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        token = client.cookies["csrftoken"].value

        response = client.post(
            login_url,
            {
                "username": "unknown-user",
                "password": "incorrect-password",
                "csrfmiddlewaretoken": token,
            },
        )

        # Bad credentials are expected; a 403 would mean CSRF rejected a
        # token that was issued with this form.
        self.assertEqual(response.status_code, 200)


class RegistrationTests(TestCase):
    def test_invalid_registration_marks_the_field_and_displays_its_error(self):
        response = self.client.post(
            reverse("accounts:register"),
            {"username": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-group has-error"')
        self.assertContains(response, "This field is required.")

    def test_successful_registration_redirects_to_login_without_authenticating(self):
        Role.objects.create(name="Member")

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-member",
                "email": "member@example.com",
                "phone": "+94771234567",
                "mc_number": "mc112202",
                "cpm_number": "cpm25666",
                "password1": "A-strong-password-123",
                "password2": "A-strong-password-123",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(username="new-member").exists())
        self.assertNotIn("_auth_user_id", self.client.session)
