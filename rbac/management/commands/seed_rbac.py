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
    {
        "codename": "report_incident",
        "name": "Report Incident",
        "description": "Submit a new incident report with photos.",
        "url_name": "incidents:report",
        "menu_label": "Report Incident",
        "menu_icon": "fa-triangle-exclamation",
        "menu_order": 20,
    },
]

DEFAULT_STAFF_ROLES = [
    {
        "name": "Security",
        "description": "Campus security and safety response.",
    },
    {
        "name": "IT Support",
        "description": "Information systems and network issues.",
    },
    {
        "name": "Student Affairs",
        "description": "Student welfare and non-academic support.",
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
        member, _ = Role.objects.get_or_create(
            name="Member",
            defaults={
                "description": "Default role for self-registered users.",
                "is_end_user_role": True,
            },
        )
        Role.objects.filter(name="Member").update(is_end_user_role=True)
        member.permissions.set(
            Permission.objects.filter(
                codename__in=("view_dashboard", "report_incident")
            )
        )

        for staff in DEFAULT_STAFF_ROLES:
            Role.objects.update_or_create(
                name=staff["name"],
                defaults={
                    "description": staff["description"],
                    "is_end_user_role": False,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Permissions synced ({created} created, "
                f"{len(DEFAULT_PERMISSIONS) - created} updated). "
                f"Default Member role ready."
            )
        )
