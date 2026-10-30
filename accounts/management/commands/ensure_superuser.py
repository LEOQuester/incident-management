from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from accounts.superuser_env import get_superuser_config
from rbac.superuser_access import assign_system_administrator_role


class Command(BaseCommand):
    help = (
        "Create or update the admin superuser from .env / environment variables. "
        "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, and optionally "
        "DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PHONE. Runs on each deploy "
        "when those variables are present. Always runs seed_rbac and attaches the "
        "System Administrator role (Users, Roles, Permissions, etc.)."
    )

    def handle(self, *args, **options):
        try:
            config = get_superuser_config()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if not config:
            self.stdout.write(
                "Skipping superuser bootstrap — set DJANGO_SUPERUSER_USERNAME and "
                "DJANGO_SUPERUSER_PASSWORD in .env (or Railway variables)."
            )
            return

        call_command("seed_rbac")

        User = get_user_model()
        username = config["username"]

        user = User.objects.filter(username=username).first()
        if user is None and config["email"]:
            user = User.objects.filter(email__iexact=config["email"]).first()
        if user is None and config["phone"]:
            user = User.objects.filter(phone=config["phone"]).first()

        created = user is None
        if created:
            user = User(username=username)

        user.username = username
        if config["email"]:
            user.email = config["email"]
        if config["phone"]:
            user.phone = config["phone"]
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(config["password"])
        user.save()

        if not assign_system_administrator_role(user):
            raise CommandError(
                "System Administrator role is missing after seed_rbac. "
                "Check rbac seed output and try again."
            )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' updated from .env.")
            )
        self.stdout.write(
            self.style.SUCCESS(
                "System Administrator role assigned (manage_users, manage_roles, "
                "manage_permissions, view_permissions, and all app features)."
            )
        )
