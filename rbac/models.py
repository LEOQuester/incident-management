from django.db import models


class Permission(models.Model):
    """Application feature permission (not Django auth.Permission)."""

    codename = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django URL name for sidebar navigation (optional).",
    )
    menu_label = models.CharField(max_length=100, blank=True)
    menu_icon = models.CharField(max_length=50, blank=True, default="fa-circle")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def sidebar_label(self) -> str:
        return self.menu_label or self.name


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
