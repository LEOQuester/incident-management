from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("incidents", "0004_incident_case_resolution_note_required"),
        ("accounts", "0004_user_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="authority",
            field=models.ForeignKey(
                blank=True,
                help_text="Authority unit this user belongs to (staff handling assigned cases).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="staff_users",
                to="incidents.authority",
            ),
        ),
    ]
