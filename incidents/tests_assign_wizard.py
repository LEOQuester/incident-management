import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from incidents.models import Incident
from rbac.models import Permission, Role


class AssignWizardTests(TestCase):
    def setUp(self):
        call_command("seed_rbac", stdout=StringIO())
        self.reporter = User.objects.create_user(username="student2", email="s2@example.test")
        self.manager = User.objects.create_user(username="manager2", email="m2@example.test")
        self.worker = User.objects.create_user(username="worker2", email="w2@example.test")
        for user, code in (
            (self.reporter, "report_incident"),
            (self.manager, "manage_cases"),
            (self.worker, "update_allocated_cases"),
        ):
            permission = Permission.objects.get(codename=code)
            role = Role.objects.create(name=f"role-{code}-{user.username}")
            role.permissions.add(permission)
            user.roles.add(role)
        from incidents.models import Authority, Category

        self.category = Category.objects.get(name="IT")
        self.authority = Authority.objects.get(name="IT Department")
        self.unit_role = Role.objects.get(name="Department Head")
        worker_role = self.worker.roles.first()
        worker_role.authority = self.authority
        worker_role.save(update_fields=["authority"])
        self.worker.roles.add(self.unit_role)
        self.case = Incident.objects.create(
            reporter=self.reporter,
            title="Wizard assign",
            description="Needs assignment",
            category=self.category,
        )

    def test_wizard_assigns_authority_and_person(self):
        self.client.force_login(self.manager)
        options = self.client.get(reverse("incidents:assign_options", args=[self.case.pk]))
        self.assertEqual(options.status_code, 200)
        payload = options.json()
        self.assertTrue(any(a["name"] == "IT Department" for a in payload["authorities"]))

        users = self.client.get(
            reverse("incidents:assign_options", args=[self.case.pk]),
            {"authority_id": self.authority.pk},
        ).json()["users"]
        self.assertTrue(any(u["id"] == self.worker.pk for u in users))

        response = self.client.post(
            reverse("incidents:assign_submit", args=[self.case.pk]),
            data=json.dumps(
                {
                    "authority_id": self.authority.pk,
                    "assignee_id": self.worker.pk,
                    "comment": "Please handle this.",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.authority_id, self.authority.pk)
        self.assertEqual(self.case.assignee_id, self.worker.pk)
        self.assertEqual(self.case.status, "assigned")
        self.assertTrue(self.case.reviewed_at)

    def test_reporter_cannot_assign(self):
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:assign_options", args=[self.case.pk]))
        self.assertEqual(response.status_code, 403)

    def test_wizard_requires_assignee(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("incidents:assign_submit", args=[self.case.pk]),
            data=json.dumps(
                {
                    "authority_id": self.authority.pk,
                    "assignee_id": None,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("responsible person", response.json()["error"].lower())
