"""Case assignment: choose authority, then responsible person."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from accounts.models import User
from incidents.models import Authority, Incident
from incidents.services.workflow import record_update


TERMINAL_STATUSES = frozenset({"closed", "rejected", "solved"})


def user_can_assign_via_wizard(user, incident: Incident) -> bool:
    if not user.is_authenticated or not user.has_rbac_permission("manage_cases"):
        return False
    return incident.status not in TERMINAL_STATUSES


def list_wizard_authorities():
    return list(
        Authority.objects.filter(is_active=True).order_by("name").values("id", "name")
    )


def list_wizard_staff(authority_id: int):
    authority = Authority.objects.filter(pk=authority_id, is_active=True).first()
    if not authority:
        return []
    users = (
        User.objects.filter(is_active=True, roles__authority=authority)
        .distinct()
        .order_by("username")
    )
    return [
        {
            "id": user.pk,
            "username": user.username,
            "display_name": user.get_display_name(),
            "email": user.email or "",
        }
        for user in users
    ]


def apply_wizard_assignment(
    *,
    incident: Incident,
    actor: User,
    authority_id: int,
    assignee_id: int,
    comment: str = "",
):
    if not user_can_assign_via_wizard(actor, incident):
        raise PermissionDenied("You cannot assign this case.")

    authority = Authority.objects.filter(pk=authority_id, is_active=True).first()
    if not authority:
        raise ValidationError("Choose a valid authority.")

    assignee = User.objects.filter(
        pk=assignee_id,
        is_active=True,
        roles__authority=authority,
    ).first()
    if not assignee:
        raise ValidationError(
            "Choose a responsible person with a role for the selected authority."
        )

    before = {
        "status": incident.status,
        "category_id": incident.category_id,
        "priority": incident.priority,
        "authority_id": incident.authority_id,
        "assignee_id": incident.assignee_id,
        "resolution_note": incident.resolution_note,
    }

    incident.authority = authority
    incident.assignee = assignee
    if incident.status not in {"assigned", "in_progress", "waiting"}:
        incident.status = Incident.Status.ASSIGNED
    now = timezone.now()
    if not incident.reviewed_at:
        incident.reviewed_at = now
    incident.save()

    note = (comment or "").strip()
    if not note:
        note = f"Assigned to {authority.name} ({assignee.get_display_name()})."
    record_update(incident, actor, before, note, internal=False)
    return incident
