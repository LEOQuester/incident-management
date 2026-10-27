import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from incidents.access import incidents_queryset_for_user
from incidents.forms import (ReportIncidentForm, CaseUpdateForm, AuthorityForm,
                            CategoryForm, validate_evidence)
from incidents.models import (Incident, IncidentPhoto, Notification, Attachment,
                              Authority, Category, CaseUpdate)
from incidents.services.workflow import save_evidence, notify_reviewers, record_update
from rbac.decorators import permission_required


@login_required
@permission_required("report_incident")
def report_incident(request):
    form = ReportIncidentForm(request.POST or None)
    files = request.FILES.getlist("photos") + request.FILES.getlist("evidence")
    if request.method == "POST":
        valid = form.is_valid()
        try:
            validate_evidence(files)
        except ValidationError as exc:
            form.add_error(None, exc)
            valid = False
        if valid:
            with transaction.atomic():
                incident = form.save(commit=False)
                incident.reporter = request.user
                incident.save()
                save_evidence(incident, files, request.user)
                CaseUpdate.objects.create(incident=incident, actor=request.user,
                                          changes={"status": {"old": None, "new": "submitted"}})
                notify_reviewers(incident)
            messages.success(request, f"Case {incident.case_number} submitted for review.")
            return redirect("incidents:detail", pk=incident.pk)
    return render(request, "incidents/report.html", {"form": form, "page_title": "Submit Complaint / Suggestion"})


@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(incidents_queryset_for_user(request.user), pk=pk)
    manager = request.user.has_rbac_permission("manage_cases")
    authority = (request.user.has_rbac_permission("update_cases") and incident.authority_id
                 and incident.authority.members.filter(pk=request.user.pk).exists())
    updates = incident.updates.select_related("actor")
    if not (manager or authority or request.user.has_rbac_permission("view_reports")):
        updates = updates.filter(internal=False)
    return render(request, "incidents/detail.html", {
        "incident": incident, "page_title": incident.case_number,
        "can_update": manager or authority, "updates": updates,
    })


@login_required
def case_update(request, pk):
    manager = request.user.has_rbac_permission("manage_cases")
    with transaction.atomic():
        incident = get_object_or_404(Incident.objects.select_for_update().filter(
            pk__in=incidents_queryset_for_user(request.user).values("pk")), pk=pk)
        authority = (request.user.has_rbac_permission("update_cases") and incident.authority_id
                     and incident.authority.members.filter(pk=request.user.pk).exists())
        if not (manager or authority):
            return HttpResponseForbidden("Case update permission required.")
        before = {field: getattr(incident, field) for field in
                  ("status", "category_id", "priority", "authority_id", "resolution_note")}
        form = CaseUpdateForm(request.POST or None, instance=incident, manager=manager)
        files = request.FILES.getlist("evidence")
        if request.method == "POST":
            valid = form.is_valid()
            try:
                validate_evidence(files)
            except ValidationError as exc:
                form.add_error(None, exc)
                valid = False
            if valid:
                incident = form.save(commit=False)
                now = timezone.now()
                if manager and not incident.reviewed_at:
                    incident.reviewed_at = now
                if incident.status == "in_progress" and not incident.started_at:
                    incident.started_at = now
                if incident.status == "solved" and before["status"] != "solved":
                    incident.solved_at = now
                if incident.status == "closed":
                    incident.closed_at = now
                if incident.status == "reopened":
                    incident.solved_at = incident.closed_at = None
                incident.save()
                save_evidence(incident, files, request.user, completion=True)
                record_update(incident, request.user, before, form.cleaned_data["comment"], form.cleaned_data["internal"])
                messages.success(request, "Case updated.")
                return redirect("incidents:detail", pk=pk)
    return render(request, "incidents/form.html", {"form": form, "page_title": f"Update {incident.case_number}", "evidence": True})


@login_required
def attachment_download(request, pk, legacy=False):
    model = IncidentPhoto if legacy else Attachment
    attachment = get_object_or_404(model, pk=pk,
        incident__in=incidents_queryset_for_user(request.user))
    file = attachment.image if legacy else attachment.file
    response = FileResponse(file.open("rb"), as_attachment=True, filename=file.name.rsplit("/", 1)[-1])
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
def case_queue(request):
    user = request.user
    if not any(user.has_rbac_permission(p) for p in ("manage_cases", "view_reports", "update_cases")):
        return HttpResponseForbidden("Staff case access required.")
    cases = incidents_queryset_for_user(user).select_related("category", "authority", "reporter")
    if not (user.has_rbac_permission("manage_cases") or user.has_rbac_permission("view_reports")):
        cases = cases.filter(authority__members=user).distinct()
    errors = []
    for key in ("status", "priority", "category", "authority", "case_type"):
        value = request.GET.get(key)
        if value:
            if key in {"category", "authority"} and not value.isdecimal():
                errors.append(f"Invalid {key}.")
                cases = cases.none()
            else:
                cases = cases.filter(**{key: value})
    for key, lookup in (("from", "created_at__date__gte"), ("to", "created_at__date__lte")):
        value = request.GET.get(key)
        if value:
            try:
                cases = cases.filter(**{lookup: date.fromisoformat(value)})
            except ValueError:
                errors.append("Use valid dates in YYYY-MM-DD format.")
                cases = cases.none()
    query = request.GET.get("q", "").strip()
    if query:
        search = Q(title__icontains=query) | Q(description__icontains=query)
        case_id = query.rsplit("-", 1)[-1]
        if case_id.isdecimal():
            search |= Q(pk=int(case_id))
        cases = cases.filter(search)
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="cases.csv"'
        writer = csv.writer(response)
        writer.writerow(["Case", "Title", "Type", "Priority", "Status", "Category", "Authority", "Age days"])
        for case in cases:
            values = [case.case_number, case.title, case.get_case_type_display(), case.priority, case.status,
                      str(case.category or ""), str(case.authority or ""), case.age_days]
            writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in values])
        return response
    summary = {"Total": cases.count(), "Attempted": cases.exclude(reviewed_at=None).count(),
               "Not attempted": cases.filter(reviewed_at=None).count(),
               "Open": cases.exclude(status__in=["closed", "rejected"]).count(),
               "Not started": cases.filter(status__in=["not_started", "assigned"]).count()}
    for status, label in (("solved", "Solved"), ("closed", "Closed")):
        summary[label] = cases.filter(status=status).count()
    for priority in ("urgent", "normal"):
        summary[priority.title()] = cases.filter(priority=priority).count()
    summary["In progress"] = cases.filter(status="in_progress").count()
    summary["Solved this month"] = cases.filter(solved_at__year=timezone.localdate().year,
                                                 solved_at__month=timezone.localdate().month).count()
    completed = cases.filter(status__in=["solved", "closed"]).count()
    summary["Resolution rate (%)"] = round(completed * 100 / summary["Total"], 1) if summary["Total"] else 0
    durations = [(c.solved_at - c.created_at).total_seconds() / 86400 for c in cases if c.solved_at]
    summary["Average resolution days"] = round(sum(durations) / len(durations), 1) if durations else 0
    authority_counts = list(cases.order_by().values("authority__name").annotate(
        total=Count("pk"),
        pending=Count("pk", filter=~Q(status__in=["solved", "closed", "rejected"])),
        assigned=Count("pk", filter=Q(status="assigned")),
        in_progress=Count("pk", filter=Q(status="in_progress")),
        not_started=Count("pk", filter=Q(status="not_started"))))
    for row in authority_counts:
        ages = [case.age_days for case in cases if (case.authority.name if case.authority else None) == row["authority__name"]
                and case.status not in {"solved", "closed", "rejected"}]
        row["average_age"] = round(sum(ages) / len(ages), 1) if ages else 0
    return render(request, "incidents/queue.html", {
        "page_title": "Case Management and Reports", "cases": cases[:200], "summary": summary,
        "statuses": Incident.Status.choices, "categories": Category.objects.all(), "authorities": Authority.objects.all(),
        "errors": errors, "ageing": cases.filter(status__in=["not_started", "assigned"]).order_by("created_at")[:100],
        "authority_counts": authority_counts,
        "category_counts": cases.values("category__name").annotate(total=Count("pk")),
        "type_counts": cases.values("case_type").annotate(total=Count("pk")),
    })


@permission_required("manage_catalogs")
def catalog_home(request):
    return redirect("incidents:catalog", kind="authorities")


@permission_required("manage_catalogs")
def catalog(request, kind, pk=None):
    if kind not in {"authorities", "categories"}:
        from django.http import Http404
        raise Http404
    model, form_class = (Authority, AuthorityForm) if kind == "authorities" else (Category, CategoryForm)
    obj = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST or None, instance=obj)
    if request.method == "POST":
        if request.POST.get("action") == "delete" and obj:
            try:
                obj.delete()
            except ProtectedError:
                messages.error(request, "This record is used by cases. Deactivate it instead.")
            return redirect("incidents:catalog", kind=kind)
        if form.is_valid():
            form.save()
            return redirect("incidents:catalog", kind=kind)
    return render(request, "incidents/catalog.html", {
        "form": form, "items": model.objects.all(), "kind": kind, "object": obj, "page_title": kind.title(),
    })


@login_required
def notifications_list(request):
    qs = Notification.objects.filter(user=request.user).select_related("incident")
    if request.method == "POST" and "mark_all_read" in request.POST:
        qs.filter(is_read=False).update(is_read=True)
        return redirect("incidents:notifications")
    return render(request, "incidents/notifications.html", {"notifications": qs[:100], "page_title": "Notifications"})


@login_required
@require_POST
def notification_mark_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    return redirect("incidents:notifications")
