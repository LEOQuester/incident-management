from django.core.management.base import BaseCommand

from rbac.models import Permission, Role


DEFAULT_PERMISSIONS = [
    {
        "codename": "view_dashboard",
        "name": "View Dashboard",
        "description": "Access the main dashboard after login.",
        "url_name": "portal:dashboard",
        "menu_label": "Dashboard",
        "menu_icon": "fa-home",
        "menu_order": 10,
    },
]


class Command(BaseCommand):
    help = "Seed default RBAC permissions for FMSC Incident Management."

    def handle(self, *args, **options):
        created = 0
        for data in DEFAULT_PERMISSIONS:
            _, was_created = Permission.objects.update_or_create(
                codename=data["codename"],
                defaults=data,
            )
            if was_created:
                created += 1
        role, _ = Role.objects.get_or_create(
            name="Member",
            defaults={"description": "Default role for self-registered users."},
        )
        role.permissions.set(Permission.objects.filter(codename="view_dashboard"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Permissions synced ({created} created, "
                f"{len(DEFAULT_PERMISSIONS) - created} updated). "
                f"Default Member role ready."
            )
        )
