from django.db.models import Q, QuerySet

from accounts.models import User
from incidents.models import Incident

VIEW_ALLOCATED_CODENAMES = frozenset(
    {"view_allocated_cases", "update_allocated_cases", "transfer_case"}
)
UPDATE_ALLOCATED_CODENAMES = frozenset({"update_allocated_cases"})
TRANSFER_CASE_CODENAMES = frozenset({"transfer_case"})
QUEUE_ACCESS_CODENAMES = frozenset(
    {
        "manage_cases",
        "view_reports",
        "view_allocated_cases",
        "update_allocated_cases",
        "transfer_case",
    }
)
REPORTER_EDIT_BLOCKED_STATUSES = frozenset({"solved", "closed", "rejected"})


def _has_any(user: User, codenames: frozenset[str]) -> bool:
    return any(user.has_rbac_permission(code) for code in codenames)


def authority_ids_for_user(user: User) -> list[int]:
    return list(
        user.roles.filter(authority__isnull=False)
        .values_list("authority_id", flat=True)
        .distinct()
    )


def user_serves_authority(user: User, authority_id: int | None) -> bool:
    if not authority_id:
        return False
    return authority_id in authority_ids_for_user(user)


def user_can_view_allocated(user: User, incident: Incident) -> bool:
    if not _has_any(user, VIEW_ALLOCATED_CODENAMES):
        return False
    return user_serves_authority(user, incident.authority_id)


def user_can_update_allocated(user: User, incident: Incident) -> bool:
    if not _has_any(user, UPDATE_ALLOCATED_CODENAMES):
        return False
    return user_serves_authority(user, incident.authority_id)


def user_can_transfer_case(user: User, incident: Incident) -> bool:
    if user.has_rbac_permission("manage_cases"):
        return True
    if not _has_any(user, TRANSFER_CASE_CODENAMES):
        return False
    return user_serves_authority(user, incident.authority_id)


def user_can_edit_own_submission(user: User, incident: Incident) -> bool:
    """Reporters may amend their submission until the case is solved, closed, or rejected."""
    if not user.is_authenticated or incident.reporter_id != user.pk:
        return False
    if not user.has_rbac_permission("report_incident"):
        return False
    return incident.status not in REPORTER_EDIT_BLOCKED_STATUSES


def incidents_queryset_for_user(user: User) -> QuerySet[Incident]:
    """Incidents the user reported or that belong to their authority unit(s) via roles."""
    if user.has_rbac_permission("manage_cases") or user.has_rbac_permission("view_reports"):
        return Incident.objects.all()
    filters = Q(reporter=user)
    if _has_any(user, VIEW_ALLOCATED_CODENAMES):
        auth_ids = authority_ids_for_user(user)
        if auth_ids:
            filters |= Q(authority_id__in=auth_ids)
    return Incident.objects.filter(filters).distinct()


def user_can_view_incident(user: User, incident: Incident) -> bool:
    return incidents_queryset_for_user(user).filter(pk=incident.pk).exists()


def can_view_internal_case_updates(user: User, incident: Incident) -> bool:
    """Internal notes are never shown to the reporter of the case."""
    if incident.reporter_id == user.pk:
        return False
    if user.has_rbac_permission("manage_cases") or user.has_rbac_permission("view_reports"):
        return True
    return user_can_view_allocated(user, incident) or user_can_update_allocated(user, incident)
