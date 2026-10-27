"""Case history and notifications for the manual review workflow."""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from accounts.models import User
from incidents.models import Attachment, CaseUpdate, Notification

logger = logging.getLogger(__name__)


def notify(users, incident, message):
    recipients = {user.pk: user for user in users if user.is_active}
    Notification.objects.bulk_create([
        Notification(user=user, incident=incident, message=message[:500])
        for user in recipients.values()
    ])
    emails = [user.email for user in recipients.values() if user.email]
    if emails:
        def deliver():
            try:
                for email in emails:
                    send_mail(f"FMSC case {incident.case_number}", message,
                              settings.DEFAULT_FROM_EMAIL, [email])
            except Exception:
                logger.exception("Case notification email delivery failed")
        transaction.on_commit(deliver)


def save_evidence(incident, files, user, completion=False):
    for uploaded in files:
        Attachment.objects.create(incident=incident, file=uploaded, uploaded_by=user,
                                  content_type=uploaded.content_type, is_completion=completion)


def notify_reviewers(incident):
    notify(reviewers(), incident, f"New case {incident.case_number}: {incident.title}")


def reviewers():
    return User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(roles__permissions__codename="manage_cases")
    ).distinct()


def record_update(incident, actor, before, comment="", internal=False):
    fields = ("status", "category_id", "priority", "authority_id", "resolution_note")
    changes = {field: {"old": before[field], "new": getattr(incident, field)}
               for field in fields if before[field] != getattr(incident, field)}
    CaseUpdate.objects.create(incident=incident, actor=actor, comment=comment,
                              internal=internal, changes=changes)
    if "authority_id" in changes and incident.authority:
        notify(incident.authority.members.all(), incident,
               f"Case {incident.case_number} assigned to {incident.authority.name}: {incident.title}")
    if "status" in changes:
        text = f"Case {incident.case_number}: {incident.get_status_display()}."
        if incident.status == "solved":
            text += f" Resolution: {incident.resolution_note}"
        notify([incident.reporter], incident, text)
