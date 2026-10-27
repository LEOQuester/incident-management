from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from incidents.models import Incident
from incidents.services.workflow import notify, reviewers


class Command(BaseCommand):
    help = "Send pending-case reminders; schedule daily using your hosting scheduler."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=max(1, options["days"]))
        cases = Incident.objects.filter(created_at__lte=cutoff).exclude(status__in=["solved", "closed", "rejected"])
        count = 0
        for case in cases.select_related("authority"):
            message = f"Pending case reminder: {case.case_number}, age {case.age_days} days."
            # Avoid duplicate reminders when a daily scheduler retries.
            if case.notifications.filter(message=message, created_at__date=timezone.localdate()).exists():
                continue
            if case.authority and case.authority.is_active:
                notify(case.authority.members.all(), case, message)
            else:
                notify(reviewers(), case, message)
            count += 1
        self.stdout.write(f"Processed {count} pending cases.")
