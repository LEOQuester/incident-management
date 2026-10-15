from django.db import models


class Permission(models.Model):
    """Assignable permission codename (metadata lives in rbac.features.APP_FEATURES)."""

    codename = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_end_user_role = models.BooleanField(
        default=False,
        help_text="End-user roles (e.g. Member) are excluded from AI incident routing.",
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
