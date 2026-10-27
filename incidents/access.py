from django.db.models import Q, QuerySet

from accounts.models import User
from incidents.models import Incident


def incidents_queryset_for_user(user: User) -> QuerySet[Incident]:
    """Incidents the user reported or that were routed to one of their roles."""
    if user.is_superuser or user.has_rbac_permission("manage_cases") or user.has_rbac_permission("view_reports"):
        return Incident.objects.all()
    filters = Q(reporter=user)
    if user.has_rbac_permission("update_cases"):
        filters |= Q(authority__members=user)
    return Incident.objects.filter(filters).distinct()


def user_can_view_incident(user: User, incident: Incident) -> bool:
    return incidents_queryset_for_user(user).filter(pk=incident.pk).exists()
