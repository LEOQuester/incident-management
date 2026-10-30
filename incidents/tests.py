from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from accounts.models import User
from rbac.models import Role, Permission
from incidents.models import Incident, Authority, Category, Attachment, Notification
from incidents.forms import validate_evidence
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
                             "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class WorkflowTests(TestCase):
    def setUp(self):
        call_command("seed_rbac", stdout=StringIO())
        self.reporter = User.objects.create_user(username="student", email="student@example.test")
        self.other = User.objects.create_user(username="other", email="other@example.test")
        self.manager = User.objects.create_user(username="manager", email="manager@example.test")
        self.worker = User.objects.create_user(username="worker", email="worker@example.test")
        self.viewer = User.objects.create_user(username="viewer", email="viewer@example.test")
        for user, code in ((self.reporter, "report_incident"), (self.manager, "manage_cases"),
                           (self.worker, "update_allocated_cases"), (self.viewer, "view_reports")):
            permission, _ = Permission.objects.get_or_create(codename=code, defaults={"name": code})
            role = Role.objects.create(name=code)
            role.permissions.add(permission)
            user.roles.add(role)
        self.category = Category.objects.get(name="IT")
        self.authority = Authority.objects.get(name="IT Department")
        worker_role = self.worker.roles.first()
        worker_role.authority = self.authority
        worker_role.save(update_fields=["authority"])
        unit_role = Role.objects.get(name="Department Head")
        self.worker.roles.add(unit_role)
        self.case = Incident.objects.create(reporter=self.reporter, title="Broken projector",
                                            description="The classroom projector is not working", category=self.category)

    def update(self, user, **data):
        self.client.force_login(user)
        return self.client.post(reverse("incidents:update", args=[self.case.pk]), data)

    def test_submission_and_unique_case_number(self):
        self.client.force_login(self.reporter)
        response = self.client.post(reverse("incidents:report"), {
            "title": "Add classroom seating", "description": "Please provide more seating in the classroom",
            "case_type": "suggestion", "category": self.category.pk,
            "location": "Hall A",
        })
        self.assertEqual(response.status_code, 302)
        created = Incident.objects.latest("pk")
        self.assertEqual(created.status, "submitted")
        self.assertNotEqual(created.case_number, self.case.case_number)
        self.assertTrue(created.updates.exists())
        self.assertTrue(Notification.objects.filter(user=self.manager, incident=created).exists())

    def test_assignment_solve_and_close(self):
        response = self.update(self.manager, status="assigned", priority="urgent", category=self.category.pk,
                               authority=self.authority.pk, comment="Please investigate")
        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.authority, self.authority)
        self.assertTrue(self.case.reviewed_at)
        self.assertTrue(Notification.objects.filter(user=self.worker).exists())
        response = self.update(self.worker, comment_type="resolution", comment="")
        self.assertEqual(response.status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, "assigned")
        response = self.update(
            self.worker,
            comment_type="resolution",
            comment="Replaced the projector",
        )
        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertIsNotNone(self.case.solved_at)
        self.assertTrue(Notification.objects.filter(user=self.reporter, message__contains="Replaced the projector").exists())
        response = self.update(
            self.manager,
            status="closed",
            priority="urgent",
            category=self.category.pk,
            authority=self.authority.pk,
        )
        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertIsNotNone(self.case.closed_at)
        self.assertEqual(self.case.updates.count(), 3)

    def test_case_and_attachment_privacy(self):
        attachment = Attachment.objects.create(incident=self.case, uploaded_by=self.reporter,
            file=SimpleUploadedFile("test.mp4", b"evidence"), content_type="video/mp4")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("incidents:detail", args=[self.case.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("incidents:attachment", args=[attachment.pk])).status_code, 404)
        self.client.force_login(self.reporter)
        self.assertEqual(self.client.get(reverse("incidents:attachment", args=[attachment.pk])).status_code, 200)
        self.assertEqual(self.client.get("/media/" + attachment.file.name).status_code, 404)

    def test_reporter_and_viewer_cannot_update(self):
        self.assertEqual(self.update(self.reporter, status="solved").status_code, 403)
        self.assertEqual(self.update(self.viewer, status="solved").status_code, 403)
        self.assertEqual(self.update(self.worker, status="solved").status_code, 404)

    def test_reporter_can_edit_own_submission(self):
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:edit", args=[self.case.pk]))
        self.assertEqual(response.status_code, 200)
        detail = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertContains(detail, "Edit submission")
        response = self.client.post(
            reverse("incidents:edit", args=[self.case.pk]),
            {
                "title": "Broken projector (updated)",
                "description": "The classroom projector is not working; happened Monday",
                "case_type": "complaint",
                "category": self.category.pk,
                "location": "Room 12",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.title, "Broken projector (updated)")
        self.assertEqual(self.case.location, "Room 12")
        update = self.case.updates.order_by("-pk").first()
        self.assertIn("title", update.changes)

    def test_reporter_cannot_edit_solved_case(self):
        self.case.status = "solved"
        self.case.resolution_note = "Fixed"
        self.case.save(update_fields=["status", "resolution_note"])
        self.client.force_login(self.reporter)
        self.assertEqual(self.client.get(reverse("incidents:edit", args=[self.case.pk])).status_code, 403)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertNotContains(response, "Edit submission")

    def test_other_user_cannot_edit_submission(self):
        permission = Permission.objects.get(codename="report_incident")
        role = Role.objects.create(name="other_reporter")
        role.permissions.add(permission)
        self.other.roles.add(role)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("incidents:edit", args=[self.case.pk])).status_code, 404)

    def test_internal_notes_hidden_from_reporter(self):
        self.case.updates.create(actor=self.manager, comment="Private staff note", internal=True)
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertNotContains(response, "Private staff note")

    def test_internal_comment_does_not_require_resolution_type(self):
        self.update(
            self.manager,
            status="assigned",
            priority="normal",
            category=self.category.pk,
            authority=self.authority.pk,
            comment="Please handle",
        )
        response = self.update(
            self.worker,
            comment_type="internal",
            comment="Staff-only progress note",
            status="in_progress",
        )
        self.assertEqual(response.status_code, 302)
        note = self.case.updates.filter(comment="Staff-only progress note").first()
        self.assertIsNotNone(note)
        self.assertTrue(note.internal)

    def test_reporter_never_sees_internal_notes(self):
        self.case.updates.create(
            actor=self.manager,
            comment="Staff-only note",
            internal=True,
        )
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertNotContains(response, "Staff-only note")
        self.assertNotContains(response, "case-detail-event-internal")

    def test_manager_who_reported_case_does_not_see_internal_notes(self):
        self.case.reporter = self.manager
        self.case.save(update_fields=["reporter"])
        self.case.updates.create(
            actor=self.worker,
            comment="Hidden from submitter",
            internal=True,
        )
        self.client.force_login(self.manager)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertNotContains(response, "Hidden from submitter")

    def test_detail_hides_submission_echo_in_activity(self):
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.reporter.get_display_name())
        self.assertNotContains(response, "Comments &amp; updates")
        self.case.updates.create(
            actor=self.manager,
            comment="",
            changes={"status": {"old": "submitted", "new": "assigned"}, "authority_id": {"old": None, "new": self.authority.pk}},
        )
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("incidents:detail", args=[self.case.pk]))
        self.assertContains(response, "Comments &amp; updates")
        self.assertContains(response, self.manager.get_display_name())
        self.assertContains(response, str(self.authority))

    def test_change_display_uses_names_not_ids(self):
        from incidents.templatetags.incident_media import change_value_display

        self.assertEqual(
            change_value_display(self.authority.pk, "authority_id"),
            str(self.authority),
        )
        self.assertEqual(
            change_value_display(self.worker.pk, "assignee_id"),
            self.worker.get_display_name(),
        )
        self.assertEqual(change_value_display("assigned", "status"), "Assigned")

    def test_reports_filters_and_invalid_date(self):
        self.client.force_login(self.viewer)
        self.assertContains(self.client.get(reverse("portal:dashboard")), "Broken projector")
        self.assertNotContains(
            self.client.get(reverse("portal:dashboard"), {"priority": "urgent"}),
            "Broken projector",
        )
        self.assertContains(
            self.client.get(reverse("portal:dashboard"), {"date_from": "bad"}),
            "valid date",
        )
        self.assertEqual(
            self.client.get(reverse("portal:dashboard"), {"export": "csv"})["Content-Type"],
            "text/csv; charset=utf-8",
        )
        response = self.client.get(reverse("incidents:queue"), {"from": "bad"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid date")

    def test_spoofed_image_rejected(self):
        with self.assertRaises(ValidationError):
            validate_evidence([SimpleUploadedFile("fake.png", b"not an image", content_type="image/png")])

    def test_authority_cannot_close(self):
        self.case.authority = self.authority
        self.case.save()
        self.assertEqual(self.update(self.worker, status="closed").status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, "submitted")

    def test_catalog_deactivation_and_protected_delete(self):
        permission = Permission.objects.get(codename="manage_authorities")
        role = Role.objects.create(name="Catalog administrator")
        role.permissions.add(permission)
        self.manager.roles.add(role)
        self.client.force_login(self.manager)
        self.assertContains(self.client.get(reverse("incidents:catalog", args=["authorities"])), "IT Unit")
        response = self.client.post(reverse("incidents:catalog_delete", args=["categories", self.category.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_reassignment_removes_old_authority_access(self):
        self.case.authority = self.authority
        self.case.status = "assigned"
        self.case.save()
        replacement = Authority.objects.create(name="Maintenance")
        self.update(self.manager, status="assigned", priority="normal", category=self.category.pk, authority=replacement.pk)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(reverse("incidents:detail", args=[self.case.pk])).status_code, 404)

    def test_reopen_requires_reason(self):
        self.case.status = "solved"
        self.case.resolution_note = "Fixed"
        self.case.solved_at = timezone.now()
        self.case.save()
        data = dict(status="reopened", priority="normal", category=self.category.pk)
        self.assertEqual(self.update(self.manager, **data).status_code, 200)
        self.assertEqual(self.update(self.manager, **data, comment="Still broken").status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, "reopened")
        self.assertIsNone(self.case.solved_at)

    def test_pending_reminders_are_idempotent_for_same_day(self):
        Incident.objects.filter(pk=self.case.pk).update(created_at=timezone.now() - timedelta(days=10))
        call_command("remind_pending_cases", stdout=StringIO())
        count = Notification.objects.count()
        self.assertGreater(count, 0)
        call_command("remind_pending_cases", stdout=StringIO())
        self.assertEqual(Notification.objects.count(), count)

    def test_seed_is_idempotent_and_preserves_custom_role_permissions(self):
        call_command("seed_rbac", stdout=StringIO())
        role = Role.objects.get(name="System Administrator")
        role.permissions.clear()
        call_command("seed_rbac", stdout=StringIO())
        role.refresh_from_db()
        self.assertTrue(role.permissions.filter(codename="manage_users").exists())
        for retired in ("Member", "Administrator", "IT Unit staff"):
            self.assertFalse(Role.objects.filter(name=retired).exists())
        self.assertFalse(Permission.objects.filter(codename="update_cases").exists())
        head = Role.objects.get(name="Department Head")
        self.assertTrue(
            head.permissions.filter(codename="update_allocated_cases").exists()
        )
        self.assertTrue(
            head.permissions.filter(codename="transfer_case").exists()
        )
        self.assertEqual(head.authority.name, "IT Department")

    @patch("subprocess.run")
    def test_video_stream_and_duration_validation(self, probe):
        probe.return_value = SimpleNamespace(stdout='{"format":{"duration":"20"},"streams":[{"codec_type":"video"}]}')
        video = SimpleUploadedFile("video.mp4", b"\x00\x00\x00\x18ftypisom" + b"0" * 30)
        validate_evidence([video])
        self.assertEqual(video.content_type, "video/mp4")
        probe.return_value = SimpleNamespace(stdout='{"format":{"duration":"500"},"streams":[{"codec_type":"video"}]}')
        with self.assertRaises(ValidationError):
            validate_evidence([video])

    def test_solved_email_is_sent_after_commit(self):
        from django.core import mail
        self.case.authority = self.authority
        self.case.status = "assigned"
        self.case.save()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.update(
                self.worker,
                comment_type="resolution",
                comment="Equipment replaced",
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox[-1].to, [self.reporter.email])
        self.assertIn("Equipment replaced", mail.outbox[-1].body)
