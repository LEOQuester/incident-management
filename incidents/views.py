from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from incidents import access as incident_access
from incidents.access import (
    QUEUE_ACCESS_CODENAMES,
    incidents_queryset_for_user,
    user_can_edit_own_submission,
    user_can_transfer_case,
    user_can_update_allocated,
    user_can_view_allocated,
)
from incidents.catalog_access import user_can_manage_catalog
from incidents.decorators import catalog_permission_required
from incidents.forms import (ReportIncidentForm, CaseUpdateForm, AuthorityForm,
                            CategoryForm, validate_evidence)
from incidents.models import (Incident, IncidentPhoto, Notification, Attachment,
                              Authority, Category, CaseUpdate)
from incidents.services.workflow import save_evidence, notify_reviewers, record_update, record_submission_edit
from incidents.activity_display import activity_feed_updates
from portal.pagination import paginate
from rbac.decorators import permission_required


def evidence_upload_context():
    max_bytes = settings.INCIDENT_PHOTO_MAX_BYTES
    return {
        "max_evidence": settings.INCIDENT_MAX_PHOTOS,
        "evidence_max_mb": max_bytes // (1024 * 1024),
    }


def submission_evidence_previews(incident):
    """Preview URLs for submission evidence (edit form slot grid)."""
    items = []
    for attachment in incident.attachments.filter(is_completion=False):
        content_type = attachment.content_type or ""
        if content_type.startswith("image/") or content_type.startswith("video/"):
            items.append(
                {
                    "type": "video" if content_type.startswith("video/") else "image",
                    "url": reverse("incidents:attachment_preview", args=[attachment.pk]),
                }
            )
        else:
            items.append(
                {
                    "type": "file",
                    "url": reverse("incidents:attachment", args=[attachment.pk]),
                }
            )
    for photo in incident.photos.all():
        items.append(
            {
                "type": "image",
                "url": reverse("incidents:photo_preview", args=[photo.pk]),
            }
        )
    return items


def evidence_context_for_incident(incident):
    return {
        **evidence_upload_context(),
        "existing_evidence_previews": submission_evidence_previews(incident),
    }


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
    return render(
        request,
        "incidents/report.html",
        {
            "form": form,
            "page_title": "Submit feedback",
            **evidence_upload_context(),
        },
    )


@login_required
@permission_required("report_incident")
def edit_own_incident(request, pk):
    incident = get_object_or_404(
        incidents_queryset_for_user(request.user).prefetch_related("attachments", "photos"),
        pk=pk,
    )
    if not user_can_edit_own_submission(request.user, incident):
        return HttpResponseForbidden("You cannot edit this case.")
    form = ReportIncidentForm(request.POST or None, instance=incident)
    files = request.FILES.getlist("photos") + request.FILES.getlist("evidence")
    if request.method == "POST":
        before = {
            field: getattr(incident, field)
            for field in (
                "title",
                "description",
                "location",
                "category_id",
                "case_type",
                "priority",
            )
        }
        valid = form.is_valid()
        try:
            validate_evidence(files)
        except ValidationError as exc:
            form.add_error(None, exc)
            valid = False
        if valid and incident.submission_evidence_count() + len(files) > settings.INCIDENT_MAX_PHOTOS:
            form.add_error(
                None,
                f"You can have at most {settings.INCIDENT_MAX_PHOTOS} evidence files on a case.",
            )
            valid = False
        if valid:
            with transaction.atomic():
                incident = form.save()
                save_evidence(incident, files, request.user)
                record_submission_edit(incident, request.user, before)
            messages.success(request, "Your submission was updated.")
            return redirect("incidents:detail", pk=incident.pk)
    return render(
        request,
        "incidents/report.html",
        {
            "form": form,
            "page_title": f"Edit {incident.case_number}",
            "edit_mode": True,
            "cancel_url": reverse("incidents:detail", args=[incident.pk]),
            "incident": incident,
            **evidence_context_for_incident(incident),
        },
    )


@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(
        incidents_queryset_for_user(request.user)
        .select_related("category", "authority", "reporter", "assignee")
        .prefetch_related("attachments", "photos", "updates__actor"),
        pk=pk,
    )
    manager = request.user.has_rbac_permission("manage_cases")
    unit_staff = user_can_view_allocated(request.user, incident) or user_can_update_allocated(
        request.user, incident
    )
    can_update = manager or user_can_update_allocated(request.user, incident)
    can_transfer = user_can_transfer_case(request.user, incident)
    can_edit_own = user_can_edit_own_submission(request.user, incident)
    updates = incident.updates.select_related("actor").order_by("-created_at", "-pk")
    if not incident_access.can_view_internal_case_updates(request.user, incident):
        updates = updates.filter(internal=False)
    activity_updates = activity_feed_updates(updates)
    return render(
        request,
        "incidents/detail.html",
        {
            "incident": incident,
            "page_title": incident.case_number,
            "can_update": can_update or can_transfer,
            "can_edit_own": can_edit_own,
            "updates": updates,
            "activity_updates": activity_updates,
        },
    )


@login_required
def case_update(request, pk):
    manager = request.user.has_rbac_permission("manage_cases")
    with transaction.atomic():
        incident = get_object_or_404(
            Incident.objects.select_for_update().filter(
                pk__in=incidents_queryset_for_user(request.user).values("pk")
            ),
            pk=pk,
        )
        can_update = manager or user_can_update_allocated(request.user, incident)
        can_transfer = user_can_transfer_case(request.user, incident)
        if not (manager or can_update or can_transfer):
            return HttpResponseForbidden("Case update permission required.")
        before = {
            field: getattr(incident, field)
            for field in (
                "status",
                "category_id",
                "priority",
                "authority_id",
                "assignee_id",
                "resolution_note",
            )
        }
        form = CaseUpdateForm(
            request.POST or None,
            instance=incident,
            manager=manager,
            can_transfer=can_transfer and not manager,
            can_update=can_update or manager,
        )
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
                comment_type = form.cleaned_data.get("comment_type") or CaseUpdateForm.COMMENT_TYPE_NORMAL
                internal = comment_type == CaseUpdateForm.COMMENT_TYPE_INTERNAL
                record_update(
                    incident,
                    request.user,
                    before,
                    form.cleaned_data.get("comment") or "",
                    internal=internal,
                )
                messages.success(request, "Case updated.")
                return redirect("incidents:detail", pk=pk)
    return render(
        request,
        "incidents/form.html",
        {
            "form": form,
            "page_title": f"Update {incident.case_number}",
            "evidence": True,
            **evidence_context_for_incident(incident),
        },
    )


def _attachment_response(request, pk, legacy=False, *, inline=False):
    model = IncidentPhoto if legacy else Attachment
    attachment = get_object_or_404(
        model,
        pk=pk,
        incident__in=incidents_queryset_for_user(request.user),
    )
    if legacy:
        file = attachment.image
        content_type = "image/jpeg"
    else:
        file = attachment.file
        content_type = attachment.content_type or "application/octet-stream"
    filename = file.name.rsplit("/", 1)[-1]
    response = FileResponse(file.open("rb"), as_attachment=not inline, filename=filename)
    if inline:
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        if content_type:
            response["Content-Type"] = content_type
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
def attachment_download(request, pk, legacy=False):
    return _attachment_response(request, pk, legacy, inline=False)


@login_required
def attachment_preview(request, pk, legacy=False):
    return _attachment_response(request, pk, legacy, inline=True)


@login_required
def case_queue(request):
    """Legacy URL: staff reports and case list live on the dashboard."""
    user = request.user
    if not any(user.has_rbac_permission(p) for p in QUEUE_ACCESS_CODENAMES):
        return HttpResponseForbidden("Staff case access required.")
    query = request.GET.copy()
    if "from" in query:
        query["date_from"] = query.pop("from")
    if "to" in query:
        query["date_to"] = query.pop("to")
    url = reverse("portal:dashboard")
    if query:
        url = f"{url}?{query.urlencode()}"
    return redirect(url)


@login_required
def catalog_home(request):
    if user_can_manage_catalog(request.user, "authorities"):
        return redirect("incidents:catalog_authorities")
    if user_can_manage_catalog(request.user, "categories"):
        return redirect("incidents:catalog_categories")
    messages.error(request, "You do not have permission to access this page.")
    return redirect("portal:access_denied")


@catalog_permission_required
def catalog_list(request, kind):
    if kind not in {"authorities", "categories"}:
        from django.http import Http404
        raise Http404
    model = Authority if kind == "authorities" else Category
    title = "Authorities" if kind == "authorities" else "Categories"
    if kind == "authorities":
        queryset = Authority.objects.all().order_by("name")
    else:
        queryset = Category.objects.all().order_by("name")
    page_obj, previous_url, next_url = paginate(request, queryset, per_page=25)
    return render(
        request,
        "incidents/catalog_list.html",
        {
            "page_obj": page_obj,
            "previous_url": previous_url,
            "next_url": next_url,
            "kind": kind,
            "page_title": title,
        },
    )


@catalog_permission_required
def catalog_create(request, kind):
    if kind not in {"authorities", "categories"}:
        from django.http import Http404
        raise Http404
    form_class = AuthorityForm if kind == "authorities" else CategoryForm
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Saved.")
        return redirect("incidents:catalog", kind=kind)
    title = f"New {'authority' if kind == 'authorities' else 'category'}"
    return render(
        request,
        "incidents/catalog_form.html",
        {"form": form, "kind": kind, "page_title": title},
    )


@catalog_permission_required
def catalog_edit(request, kind, pk):
    if kind not in {"authorities", "categories"}:
        from django.http import Http404
        raise Http404
    model, form_class = (Authority, AuthorityForm) if kind == "authorities" else (Category, CategoryForm)
    obj = get_object_or_404(model, pk=pk)
    form = form_class(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("incidents:catalog", kind=kind)
    title = f"Edit {'authority' if kind == 'authorities' else 'category'}"
    staff_users = []
    if kind == "authorities":
        from accounts.models import User
        staff_users = list(
            User.objects.filter(roles__authority=obj, is_active=True)
            .distinct()
            .order_by("username")
        )
    return render(
        request,
        "incidents/catalog_form.html",
        {
            "form": form,
            "kind": kind,
            "object": obj,
            "page_title": title,
            "staff_users": staff_users,
        },
    )


@catalog_permission_required
def catalog_delete(request, kind, pk):
    if kind not in {"authorities", "categories"}:
        from django.http import Http404
        raise Http404
    model = Authority if kind == "authorities" else Category
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Deleted.")
        except ProtectedError:
            messages.error(request, "This record is used by cases. Deactivate it instead.")
        return redirect("incidents:catalog", kind=kind)
    title = f"Delete {'authority' if kind == 'authorities' else 'category'}"
    return render(
        request,
        "portal/admin/confirm_delete.html",
        {
            "object": obj,
            "page_title": title,
            "cancel_url": "incidents:catalog",
            "cancel_url_kind": kind,
        },
    )


@login_required
def notifications_list(request):
    qs = Notification.objects.filter(user=request.user).select_related("incident").order_by(
        "-created_at", "-pk"
    )
    if request.method == "POST" and "mark_all_read" in request.POST:
        qs.filter(is_read=False).update(is_read=True)
        return redirect("incidents:notifications")
    page_obj, previous_url, next_url = paginate(
        request, qs, per_page=20
    )
    return render(
        request,
        "incidents/notifications.html",
        {
            "page_obj": page_obj,
            "previous_url": previous_url,
            "next_url": next_url,
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
