from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """FMSC user: login via username, email, or E.164 phone number."""

    email = models.EmailField("email address", blank=True, unique=True, null=True)
    user_type = models.CharField(max_length=20, choices=[("student", "Student"), ("lecturer", "Lecturer"), ("staff", "Staff")], default="student")
    department = models.CharField(max_length=150, blank=True)
    phone = PhoneNumberField(unique=True, blank=True, null=True)
    mc_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Management Club number, e.g. mc112202",
    )
    cpm_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="CPM number, e.g. cpm25666",
    )
    roles = models.ManyToManyField(
        "rbac.Role",
        related_name="users",
        blank=True,
    )

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_display_name()

    def get_display_name(self) -> str:
        full = self.get_full_name().strip()
        if full:
            return full
        return self.username

    def has_rbac_permission(self, codename: str) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(permissions__codename=codename).exists()

    def get_permission_codenames(self) -> set[str]:
        if self.is_superuser:
            from rbac.models import Permission

            return set(Permission.objects.values_list("codename", flat=True))
        return set(
            self.roles.values_list("permissions__codename", flat=True).distinct()
        )
