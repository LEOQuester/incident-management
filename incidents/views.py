from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from incidents.forms import ReportIncidentForm, validate_incident_photos
from incidents.models import Incident, IncidentPhoto, Notification
from incidents.services.gemini_router import route_incident
from rbac.decorators import permission_required


@login_required
@permission_required("report_incident")
def report_incident(request):
    if request.method == "POST":
        form = ReportIncidentForm(request.POST)
        photos = request.FILES.getlist("photos")
        try:
            if photos:
                validate_incident_photos(photos)
        except ValidationError as exc:
            form.add_error(None, exc)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reporter = request.user
            incident.save()
            for index, photo in enumerate(photos):
                IncidentPhoto.objects.create(
                    incident=incident,
                    image=photo,
                    sort_order=index,
                )
            notified = route_incident(incident)
            if incident.status == Incident.Status.ROUTED:
                messages.success(
                    request,
                    f"Incident submitted. {notified} staff member(s) notified.",
                )
            else:
                messages.warning(
                    request,
                    "Incident saved, but automatic routing could not run. "
                    "Staff will follow up manually.",
                )
            return redirect("incidents:report")
    else:
        form = ReportIncidentForm()

    return render(
        request,
        "incidents/report.html",
        {
            "form": form,
            "page_title": "Report Incident",
            "max_photos": settings.INCIDENT_MAX_PHOTOS,
            "max_description": settings.INCIDENT_DESCRIPTION_MAX_LENGTH,
        },
    )


@login_required
def notifications_list(request):
    qs = Notification.objects.filter(user=request.user).select_related("incident")
    if request.method == "POST" and "mark_all_read" in request.POST:
        qs.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect("incidents:notifications")

    return render(
        request,
        "incidents/notifications.html",
        {
            "notifications": qs[:100],
            "page_title": "Notifications",
        },
    )


@login_required
@require_POST
def notification_mark_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    return redirect("incidents:notifications")
