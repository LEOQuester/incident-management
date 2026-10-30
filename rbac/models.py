from django.db import models


class Permission(models.Model):
    """Assignable permission; built-in rows are synced from rbac.features.APP_FEATURES."""

    MENU_SECTION_MENU = "menu"
    MENU_SECTION_ADMIN = "admin"
    MENU_SECTION_CHOICES = (
        (MENU_SECTION_MENU, "Menu"),
        (MENU_SECTION_ADMIN, "Administration"),
    )

    codename = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    is_builtin = models.BooleanField(
        default=False,
        help_text="Synced from application code; cannot be deleted.",
    )
    show_in_menu = models.BooleanField(
        default=False,
        help_text="Show a sidebar link for users who have this permission.",
    )
    menu_label = models.CharField(max_length=100, blank=True)
    menu_icon = models.CharField(max_length=50, blank=True, default="fa-circle")
    menu_section = models.CharField(
        max_length=20,
        choices=MENU_SECTION_CHOICES,
        default=MENU_SECTION_MENU,
    )
    url_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Django URL name, e.g. portal:dashboard",
    )
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    authority = models.ForeignKey(
        "incidents.Authority",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="unit_roles",
        help_text="When set, users with this role handle cases assigned to this authority unit.",
    )
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
