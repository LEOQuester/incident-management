from django.core.management.base import BaseCommand

from rbac.features import sync_permissions_to_database
from rbac.models import Permission, Role


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
    help = "Sync app-defined permissions and default roles from code."

    def handle(self, *args, **options):
        sync_permissions_to_database()
        count = Permission.objects.count()

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
                f"Synced {count} permissions from rbac.features.APP_FEATURES. "
                f"Member role ready."
            )
        )
