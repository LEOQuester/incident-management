import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from incidents.access import incidents_queryset_for_user
from incidents.models import Incident
from incidents.services.assignment_wizard import (
    apply_wizard_assignment,
    list_wizard_authorities,
    list_wizard_staff,
    user_can_assign_via_wizard,
)


def _incident_for_assign(request, pk):
    return get_object_or_404(
        incidents_queryset_for_user(request.user).select_related("authority", "assignee"),
        pk=pk,
    )


@login_required
@require_GET
def case_assign_wizard_options(request, pk):
    incident = _incident_for_assign(request, pk)
    if not user_can_assign_via_wizard(request.user, incident):
        return HttpResponseForbidden("Assignment not allowed for this case.")

    authority_id = request.GET.get("authority_id", "").strip()

    if authority_id:
        if not authority_id.isdecimal():
            return JsonResponse({"error": "Invalid authority."}, status=400)
        return JsonResponse({"users": list_wizard_staff(int(authority_id))})

    return JsonResponse(
        {
            "case": {
                "id": incident.pk,
                "number": incident.case_number,
                "label": (incident.title or incident.description or "Case").strip()[:120],
                "title": incident.title,
                "authority": str(incident.authority) if incident.authority else "",
                "assignee": incident.assignee.get_display_name() if incident.assignee else "",
            },
            "authorities": list_wizard_authorities(),
        }
    )


@login_required
@require_POST
@transaction.atomic
def case_assign_wizard_submit(request, pk):
    incident = get_object_or_404(
        Incident.objects.select_for_update().filter(
            pk__in=incidents_queryset_for_user(request.user).values("pk")
        ),
        pk=pk,
    )
    if not user_can_assign_via_wizard(request.user, incident):
        return HttpResponseForbidden("Assignment not allowed for this case.")

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    authority_id = payload.get("authority_id")
    assignee_id = payload.get("assignee_id")
    comment = payload.get("comment", "")

    if not isinstance(authority_id, int):
        return JsonResponse({"error": "Authority is required."}, status=400)
    if not isinstance(assignee_id, int):
        return JsonResponse({"error": "A responsible person is required."}, status=400)

    from django.core.exceptions import ValidationError

    try:
        apply_wizard_assignment(
            incident=incident,
            actor=request.user,
            authority_id=authority_id,
            assignee_id=assignee_id,
            comment=str(comment) if comment is not None else "",
        )
    except ValidationError as exc:
        return JsonResponse({"error": " ".join(exc.messages)}, status=400)

    messages.success(
        request,
        f"Case {incident.case_number} assigned to {incident.authority.name}.",
    )
    return JsonResponse(
        {
            "ok": True,
            "redirect_url": reverse("incidents:detail", args=[incident.pk]),
        }
    )
