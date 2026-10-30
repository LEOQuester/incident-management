from django.core.management import call_command
from django.core.management.base import BaseCommand

from rbac.superuser_access import sync_superuser_portal_roles


class Command(BaseCommand):
    help = (
        "Run seed_rbac, then grant the System Administrator role to every active superuser "
        "(Users, Roles, Permissions, and all other portal features)."
    )

    def handle(self, *args, **options):
        call_command("seed_rbac")
        linked = sync_superuser_portal_roles()
        if linked:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Linked System Administrator role to {linked} superuser account(s)."
                )
            )
        else:
            self.stdout.write(
                "All active superusers already have the System Administrator role."
            )
