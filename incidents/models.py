from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Authority(models.Model):
    name = models.CharField(max_length=150, unique=True)
    officer_name = models.CharField(max_length=150, blank=True)
    designation = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    unit = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="authorities")

    def __str__(self):
        return self.name


class Incident(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        ROUTED = "routed", "Routed"
        ROUTING_FAILED = "routing_failed", "Routing failed"
        UNDER_REVIEW = "under_review", "Under Review"
        NOT_STARTED = "not_started", "Not Started"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        WAITING = "waiting", "Waiting for Information"
        SOLVED = "solved", "Solved"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected"
        REOPENED = "reopened", "Reopened"

    class CaseType(models.TextChoices):
        COMPLAINT = "complaint", "Complaint"
        SUGGESTION = "suggestion", "Suggestion"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=200, blank=True)
    case_type = models.CharField(max_length=20, choices=CaseType.choices, default=CaseType.COMPLAINT)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT)
    location = models.CharField(max_length=200, blank=True)
    authority = models.ForeignKey(Authority, null=True, blank=True, on_delete=models.PROTECT, related_name="cases")
    resolution_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    @property
    def case_number(self):
        return f"FMSC-{self.created_at.year}-{self.pk:06d}"

    @property
    def age_days(self):
        return max(0, (timezone.now() - self.created_at).days)

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incidents_reported",
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    ai_role_selection = models.JSONField(blank=True, null=True)
    alerted_roles = models.ManyToManyField(
        "rbac.Role",
        related_name="incidents",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(status__in=["solved", "closed"]) | ~models.Q(resolution_note=""),
                name="case_resolution_note_required",
            ),
        ]

    def __str__(self) -> str:
        return f"Incident #{self.pk} by {self.reporter.username}"


class IncidentPhoto(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="incidents/%Y/%m/%d/")
    sort_order = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification for {self.user.username}"


class Attachment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="evidence/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    content_type = models.CharField(max_length=100)
    is_completion = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class CaseUpdate(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="updates")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True)
    internal = models.BooleanField(default=False)
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
