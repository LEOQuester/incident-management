from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """FMSC user: login via username, email, or E.164 phone number."""

    email = models.EmailField("email address", blank=True, unique=True, null=True)
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
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        help_text="Profile photo (JPEG, PNG, or WebP, max 2 MB).",
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

    def get_initials(self) -> str:
        full = self.get_full_name().strip()
        if full:
            parts = full.split()
            if len(parts) >= 2:
                return (parts[0][0] + parts[-1][0]).upper()
            return parts[0][:2].upper()
        return (self.username[:2] or "??").upper()

    def get_scoped_authority_names(self) -> list[str]:
        return list(
            self.roles.filter(authority__isnull=False)
            .values_list("authority__name", flat=True)
            .distinct()
        )

    def has_rbac_permission(self, codename: str) -> bool:
        return self.roles.filter(permissions__codename=codename).exists()

    def get_permission_codenames(self) -> set[str]:
        return set(
            self.roles.values_list("permissions__codename", flat=True).distinct()
        )
