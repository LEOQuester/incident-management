"""Create a database export and evidence archive for an operator-managed backup schedule."""
import zipfile
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Export application data and local evidence to a new backup directory. Protect backups as sensitive data."

    def add_arguments(self, parser):
        parser.add_argument("destination")

    def handle(self, *args, **options):
        destination = Path(options["destination"]).resolve()
        if destination.exists():
            raise CommandError("Choose a new backup directory to avoid overwriting a backup.")
        media = Path(settings.MEDIA_ROOT).resolve()
        if destination == media or media in destination.parents:
            raise CommandError("Store backups outside the evidence directory.")
        destination.mkdir(parents=True)
        with (destination / "data.json").open("w", encoding="utf-8") as output:
            call_command("dumpdata", "accounts", "rbac", "incidents", "auth", "contenttypes",
                         natural_foreign=True, natural_primary=True, stdout=output)
        with zipfile.ZipFile(destination / "evidence.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            if media.exists():
                for file in media.rglob("*"):
                    if file.is_file() and not file.is_symlink():
                        archive.write(file, file.relative_to(media))
        self.stdout.write(self.style.SUCCESS(f"Backup created in {destination}"))
