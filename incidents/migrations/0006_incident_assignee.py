from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("incidents", "0005_authority_primary_contact"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                help_text="Unit member responsible for this case (optional; defaults to authority contact on transfer).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
