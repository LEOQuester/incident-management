from django.db.models import Q, QuerySet

from accounts.models import User
from incidents.models import Incident


def incidents_queryset_for_user(user: User) -> QuerySet[Incident]:
    """Incidents the user reported or that were routed to one of their roles."""
    if user.is_superuser:
        return Incident.objects.all()
    role_ids = user.roles.values_list("pk", flat=True)
    filters = Q(reporter=user)
    if role_ids:
        filters |= Q(alerted_roles__in=role_ids)
    return Incident.objects.filter(filters).distinct()


def user_can_view_incident(user: User, incident: Incident) -> bool:
    if user.is_superuser:
        return True
    if incident.reporter_id == user.pk:
        return True
    return incident.alerted_roles.filter(users=user).exists()
