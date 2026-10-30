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
        roles__permissions__codename="manage_cases"
    ).distinct()


def record_update(incident, actor, before, comment="", internal=False):
    fields = (
        "status",
        "category_id",
        "priority",
        "authority_id",
        "assignee_id",
        "resolution_note",
    )
    changes = {
        field: {"old": before[field], "new": getattr(incident, field)}
        for field in fields
        if before[field] != getattr(incident, field)
    }
    comment = (comment or "").strip()

    if internal and changes:
        CaseUpdate.objects.create(
            incident=incident,
            actor=actor,
            comment="",
            internal=False,
            changes=changes,
        )
        if comment:
            CaseUpdate.objects.create(
                incident=incident,
                actor=actor,
                comment=comment,
                internal=True,
                changes={},
            )
    else:
        CaseUpdate.objects.create(
            incident=incident,
            actor=actor,
            comment=comment,
            internal=internal,
            changes=changes,
        )
    if "authority_id" in changes or "assignee_id" in changes:
        recipients = []
        if incident.assignee_id:
            recipients.append(incident.assignee)
        elif incident.authority and incident.authority.primary_contact_id:
            recipients.append(incident.authority.primary_contact)
        elif incident.authority:
            recipients = list(incident.authority.staff_users())
        if recipients:
            action = "transferred to" if "authority_id" in changes else "assigned within"
            unit = incident.authority.name if incident.authority else "a unit"
            notify(
                recipients,
                incident,
                f"Case {incident.case_number} {action} {unit}: {incident.title}",
            )
    if "status" in changes:
        text = f"Case {incident.case_number}: {incident.get_status_display()}."
        if incident.status == "solved":
            text += f" Resolution: {incident.resolution_note}"
        notify([incident.reporter], incident, text)


SUBMISSION_EDIT_FIELDS = (
    "title",
    "description",
    "location",
    "category_id",
    "case_type",
    "priority",
)


def record_submission_edit(incident, actor, before):
    changes = {
        field: {"old": before[field], "new": getattr(incident, field)}
        for field in SUBMISSION_EDIT_FIELDS
        if before[field] != getattr(incident, field)
    }
    if not changes:
        return
    CaseUpdate.objects.create(
        incident=incident,
        actor=actor,
        comment="",
        internal=False,
        changes=changes,
    )
