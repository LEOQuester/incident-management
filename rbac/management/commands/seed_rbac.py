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
                codename__in=("view_dashboard", "report_incident", "view_profile")
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

        defaults = {
            "Student": ("view_dashboard", "report_incident"),
            "Lecturer": ("view_dashboard", "report_incident"),
            "Administrator": ("view_dashboard", "manage_cases"),
            "Relevant Authority": ("view_dashboard", "update_cases"),
            "Faculty Management": ("view_dashboard", "view_reports"),
            "System Administrator": ("view_dashboard", "manage_users", "manage_roles", "manage_permissions", "view_permissions", "manage_catalogs"),
        }
        for name, codenames in defaults.items():
            role, created = Role.objects.get_or_create(name=name, defaults={"is_end_user_role": name in {"Student", "Lecturer"}})
            if created:
                role.permissions.set(Permission.objects.filter(codename__in=(*codenames, "view_profile")))
        from incidents.models import Category
        for name in ("Classroom", "IT", "Maintenance", "Examination", "Other"):
            Category.objects.get_or_create(name=name)

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {count} permissions from rbac.features.APP_FEATURES. "
                f"Member role ready."
            )
        )
