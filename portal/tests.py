import csv
from datetime import timedelta
from io import StringIO
from urllib.parse import parse_qs, urlparse

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from io import StringIO

from accounts.models import User
from incidents.models import Authority, Category, Incident
from rbac.models import Permission, Role


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_rbac", stdout=StringIO())
        cls.student = User.objects.create_user(username="reporter", email="reporter@example.test")
        cls.other = User.objects.create_user(username="other", email="other@example.test")
        cls.manager = User.objects.create_user(
            username="dashboard-admin", email="admin@example.test", password="test-only"
        )
        cls.worker = User.objects.create_user(username="authority-worker", email="worker@example.test")
        cls.viewer = User.objects.create_user(username="management-viewer", email="viewer@example.test")
        cls.manager.roles.add(Role.objects.get(name="System Administrator"))
        for user, codes in (
            (cls.student, ["view_dashboard"]),
            (cls.worker, ["view_dashboard", "update_allocated_cases"]),
            (cls.viewer, ["view_dashboard", "view_reports"]),
        ):
            role = Role.objects.create(name=f"test-{user.username}")
            for code in codes:
                role.permissions.add(Permission.objects.get(codename=code))
            user.roles.add(role)
        cls.category = Category.objects.create(name="IT dashboard category")
        cls.secret_category = Category.objects.create(name="Private classroom category")
        cls.authority = Authority.objects.create(name="IT dashboard authority")
        worker_role = cls.worker.roles.first()
        worker_role.authority = cls.authority
        worker_role.save(update_fields=["authority"])
        cls.secret_authority = Authority.objects.create(name="Private authority")
        cls.now = timezone.now()
        cls.submitted = cls.make_case("Submitted projector", "submitted")
        cls.assigned = cls.make_case("Assigned projector", "assigned", priority="urgent", authority=cls.authority)
        cls.progress = cls.make_case("In-progress projector", "in_progress", authority=cls.authority, started_at=cls.now)
        cls.solved = cls.make_case("Solved projector", "solved", resolution_note="Repaired", solved_at=cls.now - timedelta(days=4))
        cls.closed = cls.make_case("Closed projector", "closed", resolution_note="Confirmed", closed_at=cls.now - timedelta(days=2))
        cls.secret = cls.make_case("PRIVATE_CASE_TITLE", "submitted", reporter=cls.other, category=cls.secret_category, authority=cls.secret_authority)

    @classmethod
    def make_case(cls, title, status, **kwargs):
        values = {"reporter": cls.student, "category": cls.category, "description": "Dashboard test description", "status": status}
        values.update(kwargs)
        case = Incident.objects.create(title=title, **values)
        Incident.objects.filter(pk=case.pk).update(created_at=cls.now - timedelta(days=10))
        return case

    def dashboard(self, user=None, **params):
        self.client.force_login(user or self.manager)
        return self.client.get(reverse("portal:dashboard"), params)

    def test_summary_semantics_and_resolution_timestamps(self):
        response = self.dashboard()
        self.assertEqual(response.status_code, 200)
        counts = {card["key"]: card["count"] for card in response.context["cards"]}
        self.assertEqual(counts["total"], 6)
        self.assertEqual(counts["unattempted"], 2)
        # Progress/assignment counts even if an older record lacks reviewed_at.
        self.assertEqual(counts["attempted"], 4)
        self.assertEqual(counts["open"], 5)
        self.assertEqual(counts["not_started"], 1)
        self.assertEqual(response.context["resolution_rate"], 33.3)
        self.assertEqual(response.context["average_resolution_days"], 7.0)
        response = self.dashboard(focus="not_started")
        self.assertEqual([case.pk for case in response.context["page_obj"]], [self.assigned.pk])
        self.assertContains(response, "Not started")
        workload = next(row for row in response.context["authority_rows"] if row["authority_id"] == self.authority.pk)
        self.assertEqual(workload["pending"], 2)
        self.assertEqual(workload["average_age_days"], 10.0)

    def test_reporter_privacy_applies_to_filters_charts_and_export(self):
        response = self.dashboard(self.student)
        self.assertEqual(response.context["total"], 5)
        self.assertNotContains(response, "PRIVATE_CASE_TITLE")
        self.assertNotContains(response, self.secret_authority.name)
        self.assertNotContains(response, self.secret_category.name)
        response = self.dashboard(self.student, export="csv")
        self.assertNotIn(b"PRIVATE_CASE_TITLE", response.content)
        self.assertEqual(len(list(csv.reader(StringIO(response.content.decode())))), 6)
        response = self.dashboard(self.student, authority=str(self.secret_authority.pk))
        self.assertFalse(response.context["valid_filters"])
        self.assertEqual(response.context["total"], 0)

    def test_authority_scope_and_no_duplicate_counts(self):
        response = self.dashboard(self.worker)
        self.assertEqual(response.context["total"], 2)
        self.assertNotContains(response, "PRIVATE_CASE_TITLE")
        # Reporter shares the worker's authority; cases must not be double-counted.
        role = self.worker.roles.first()
        self.student.roles.add(role)
        response = self.dashboard(self.student)
        self.assertEqual(response.context["total"], 5)
        self.assertEqual(response.context["average_resolution_days"], 7.0)

    def test_filters_drive_all_reports_and_drill_links_keep_filters(self):
        response = self.dashboard(priority="urgent", category=self.category.pk)
        self.assertEqual(response.context["total"], 1)
        self.assertEqual(len(response.context["status_rows"]), 1)
        self.assertEqual(response.context["authority_rows"][0]["total"], 1)
        status_url = response.context["status_rows"][0]["url"]
        params = parse_qs(urlparse(status_url).query)
        self.assertEqual(params["priority"], ["urgent"])
        self.assertEqual(params["category"], [str(self.category.pk)])

    def test_summary_focus_and_export_select_same_cases(self):
        response = self.dashboard(focus="not_started")
        self.assertEqual(response.context["total"], 6)
        self.assertEqual([case.pk for case in response.context["page_obj"]], [self.assigned.pk])
        response = self.dashboard(focus="not_started", export="csv")
        rows = list(csv.reader(StringIO(response.content.decode())))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], self.assigned.case_number)

    def test_invalid_filters_render_validation_without_broadening(self):
        for params in ({"date_from": "2026-12-30", "date_to": "2026-01-01"}, {"date_from": "invalid"}, {"authority": "999999999999999999999999999999999"}, {"status": "invalid"}, {"focus": "invalid"}):
            response = self.dashboard(**params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["total"], 0)
            self.assertFalse(response.context["valid_filters"])

    def test_pagination_search_sort_and_read_only_manager_access(self):
        for index in range(18):
            self.make_case(f"Searchable {index}", "submitted")
        response = self.dashboard(self.viewer, q="Searchable")
        self.assertEqual(response.context["page_obj"].paginator.count, 18)
        self.assertEqual(len(response.context["page_obj"]), 15)
        self.assertIn("q=Searchable", response.context["next_url"])
        response = self.dashboard(self.viewer, q="Searchable", page=2)
        self.assertEqual(len(response.context["page_obj"]), 3)
        response = self.dashboard(q=self.assigned.case_number)
        self.assertEqual(response.context["total"], 1)

    def test_empty_results_and_csv_formula_escaping(self):
        response = self.dashboard(q="no-match-for-this-title")
        self.assertEqual(response.context["total"], 0)
        self.assertIsNone(response.context["average_resolution_days"])
        self.assertContains(response, "No matching cases")
        Incident.objects.filter(pk=self.submitted.pk).update(title="=UNSAFE()")
        response = self.dashboard(export="csv", q="=UNSAFE")
        rows = list(csv.reader(StringIO(response.content.decode())))
        self.assertEqual(rows[1][1], "'=UNSAFE()")
