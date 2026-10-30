"""Permission-scoped dashboard queries and validated report filters."""

import csv
from datetime import timedelta

from django import forms
from django.core.paginator import Paginator
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone

from incidents.access import incidents_queryset_for_user
from incidents.models import Authority, Category, Incident


UNATTEMPTED = Q(reviewed_at__isnull=True, status__in=("submitted", "routed", "routing_failed"))
NOT_STARTED = Q(status__in=("not_started", "assigned"), started_at__isnull=True)
OPEN = ~Q(status__in=("closed", "rejected"))
PENDING = ~Q(status__in=("solved", "closed", "rejected"))
RESOLVED = Q(status__in=("solved", "closed"))
FOCUSES = {
    "total": ("Total cases", Q()),
    "attempted": ("Attempted", ~UNATTEMPTED),
    "unattempted": ("Not attempted", UNATTEMPTED),
    "open": ("Open", OPEN),
    "not_started": ("Not started", NOT_STARTED),
    "urgent": ("Urgent", Q(priority="urgent")),
    "normal": ("Normal", Q(priority="normal")),
    "solved": ("Solved", Q(status="solved")),
    "closed": ("Closed", Q(status="closed")),
    "in_progress": ("In progress", Q(status="in_progress")),
}


class DashboardFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False, max_length=200)
    date_from = forms.DateField(label="From", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(label="To", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status = forms.ChoiceField(label="Status", required=False, choices=[("", "All statuses"), *Incident.Status.choices])
    priority = forms.ChoiceField(label="Priority", required=False, choices=[("", "All priorities"), *Incident.Priority.choices])
    case_type = forms.ChoiceField(label="Type", required=False, choices=[("", "All types"), *Incident.CaseType.choices])
    category = forms.ModelChoiceField(label="Category", required=False, queryset=Category.objects.none(), empty_label="All categories")
    authority = forms.ModelChoiceField(label="Authority", required=False, queryset=Authority.objects.none(), empty_label="All authorities")
    focus = forms.ChoiceField(required=False, choices=[("", "All cases"), *[(key, label) for key, (label, _) in FOCUSES.items()]])

    def __init__(self, *args, visible_cases, **kwargs):
        super().__init__(*args, **kwargs)
        # Do not expose authority/category names from cases this user cannot see.
        self.fields["category"].queryset = Category.objects.filter(pk__in=visible_cases.values("category_id")).order_by("name")
        self.fields["authority"].queryset = Authority.objects.filter(pk__in=visible_cases.values("authority_id")).order_by("name")
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control form-control-compact"
        self.fields["q"].widget.attrs["placeholder"] = "Title, case no., description"

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            self.add_error("date_to", "End date must be on or after the start date.")
        return data


def _link(params, **changes):
    query = params.copy()
    for name in ("page", "export"):
        query.pop(name, None)
    for name, value in changes.items():
        if value in (None, ""):
            query.pop(name, None)
        else:
            query[name] = str(value)
    return "?" + query.urlencode()


def _csv(cases):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="dashboard-cases.csv"'
    response["Cache-Control"] = "private, no-store"
    writer = csv.writer(response)
    writer.writerow(["Case", "Title", "Type", "Priority", "Status", "Category", "Authority", "Submitted", "Age (days)"])
    for case in cases.iterator(chunk_size=500):
        row = [case.case_number, case.title, case.get_case_type_display(), case.get_priority_display(),
               case.get_status_display(), str(case.category or ""), str(case.authority or ""),
               timezone.localtime(case.created_at).isoformat(), case.age_days]
        writer.writerow(["'" + value if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))) else value for value in row])
    return response


def dashboard_context(request):
    # Collapse membership joins before aggregating so multiple authority members
    # cannot inflate case totals or weight an average more than once.
    visible = Incident.objects.filter(pk__in=incidents_queryset_for_user(request.user).values("pk"))
    form = DashboardFilterForm(request.GET, visible_cases=visible)
    valid = form.is_valid()
    cases = visible
    if valid:
        data = form.cleaned_data
        for field in ("status", "priority", "case_type", "category", "authority"):
            if data.get(field):
                cases = cases.filter(**{field: data[field]})
        if data.get("date_from"):
            cases = cases.filter(created_at__date__gte=data["date_from"])
        if data.get("date_to"):
            cases = cases.filter(created_at__date__lte=data["date_to"])
        query = data.get("q", "")
        if query:
            search = Q(title__icontains=query) | Q(description__icontains=query)
            number = query.rsplit("-", 1)[-1]
            if number.isdecimal() and len(number) <= 18:
                search |= Q(pk=int(number))
            cases = cases.filter(search)
    else:
        # Invalid filters never silently broaden the visible result set.
        cases = cases.none()
        data = {}

    now = timezone.now()
    counts = cases.aggregate(**{key: Count("pk", filter=condition, distinct=True) for key, (_, condition) in FOCUSES.items()})
    resolved_count = cases.filter(RESOLVED).count()
    duration = ExpressionWrapper(Coalesce("solved_at", "closed_at") - F("created_at"), output_field=DurationField())
    average = cases.filter(RESOLVED).filter(Q(solved_at__gte=F("created_at")) | Q(solved_at__isnull=True, closed_at__gte=F("created_at"))).aggregate(value=Avg(duration))["value"]
    cards = []
    for key, (label, _) in FOCUSES.items():
        cards.append(
            {
                "key": key,
                "label": label,
                "count": counts[key],
                "url": _link(
                    request.GET,
                    focus=key,
                    status="",
                    priority="",
                    case_type="",
                )
                + "#case-list",
            }
        )
    status_rows = []
    for row in cases.order_by().values("status").annotate(total=Count("pk", distinct=True)).order_by("-total", "status"):
        status_rows.append({"label": dict(Incident.Status.choices).get(row["status"], row["status"]),
                            "count": row["total"], "percent": round(row["total"] * 100 / counts["total"], 1),
                            "url": _link(request.GET, status=row["status"], focus="")})
    category_rows = list(cases.order_by().values("category_id", "category__name").annotate(total=Count("pk", distinct=True)).order_by("-total", "category__name")[:6])
    for row in category_rows:
        row["percent"] = round(row["total"] * 100 / counts["total"], 1)
        row["url"] = _link(request.GET, category=row["category_id"], focus="") if row["category_id"] else None
    type_rows = [{"label": label, "count": cases.filter(case_type=value).count(), "url": _link(request.GET, case_type=value, focus="")} for value, label in Incident.CaseType.choices]
    age_expression = ExpressionWrapper(Value(now) - F("created_at"), output_field=DurationField())
    authority_rows = list(cases.order_by().values("authority_id", "authority__name").annotate(
        total=Count("pk", distinct=True), pending=Count("pk", filter=PENDING, distinct=True),
        assigned=Count("pk", filter=Q(status="assigned"), distinct=True),
        in_progress=Count("pk", filter=Q(status="in_progress"), distinct=True),
        not_started=Count("pk", filter=NOT_STARTED, distinct=True),
        average_age=Avg(age_expression, filter=PENDING),
    ).order_by("-pending", "authority__name")[:10])
    for row in authority_rows:
        row["average_age_days"] = round(max(0, row["average_age"].total_seconds() / 86400), 1) if row["average_age"] is not None else None
        row["url"] = _link(request.GET, authority=row["authority_id"], focus="") if row["authority_id"] else None
    focus = data.get("focus") or request.GET.get("focus") or "total"
    if focus not in FOCUSES:
        focus = "total"
    selected = cases.filter(FOCUSES[focus][1]).select_related(
        "authority",
        "authority__primary_contact",
        "category",
        "reporter",
        "assignee",
    )
    selected = selected.order_by("-created_at", "-pk")
    if valid and request.GET.get("export") == "csv":
        return _csv(selected)
    page = Paginator(selected, 15).get_page(request.GET.get("page"))
    base_link = _link(request.GET)
    capabilities = request.user.get_permission_codenames()
    staff = bool(
        capabilities
        & {
            "manage_cases",
            "view_reports",
            "view_allocated_cases",
            "update_allocated_cases",
            "transfer_case",
        }
    )
    return {
        "page_title": "Case Dashboard", "filter_form": form, "cards": cards, "focus": focus,
        "focus_label": FOCUSES[focus][0], "total": counts["total"], "page_obj": page,
        "status_rows": status_rows, "category_rows": category_rows, "type_rows": type_rows,
        "authority_rows": authority_rows,
        "resolution_rate": round(resolved_count * 100 / counts["total"], 1) if counts["total"] else 0,
        "average_resolution_days": round(average.total_seconds() / 86400, 1) if average is not None else None,
        "export_url": _link(request.GET, export="csv"), "valid_filters": valid,
        "previous_url": base_link + "&page=" + str(page.previous_page_number()) if page.has_previous() else "",
        "next_url": base_link + "&page=" + str(page.next_page_number()) if page.has_next() else "",
        "can_report_incident": "report_incident" in capabilities,
        "staff_dashboard": staff, "all_case_access": bool(capabilities & {"manage_cases", "view_reports"}),
        "can_update_cases": bool(
            capabilities
            & {
                "manage_cases",
                "update_allocated_cases",
                "transfer_case",
            }
        ),
        "can_assign_cases": "manage_cases" in capabilities,
        "updated_at": now,
    }
