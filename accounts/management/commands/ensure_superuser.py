import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create or update a superuser from environment variables "
        "(DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, "
        "DJANGO_SUPERUSER_EMAIL). Safe to run on every deploy."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip().lower()

        if not username or not password:
            self.stdout.write(
                "Skipping superuser bootstrap (set DJANGO_SUPERUSER_USERNAME "
                "and DJANGO_SUPERUSER_PASSWORD to enable)."
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email or None,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' password updated.")
            )
