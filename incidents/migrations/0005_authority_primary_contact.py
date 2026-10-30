from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_authority_members(apps, schema_editor):
    Authority = apps.get_model("incidents", "Authority")
    User = apps.get_model("accounts", "User")
    for authority in Authority.objects.all():
        members = list(authority.members.all())
        if not members:
            continue
        member_ids = [user.pk for user in members]
        User.objects.filter(pk__in=member_ids).update(authority_id=authority.pk)
        contact = members[0]
        legacy_email = getattr(authority, "email", "") or ""
        if legacy_email:
            for user in members:
                if (user.email or "").lower() == legacy_email.lower():
                    contact = user
                    break
        authority.primary_contact_id = contact.pk
        authority.save(update_fields=["primary_contact"])


class Migration(migrations.Migration):

    dependencies = [
        ("incidents", "0004_incident_case_resolution_note_required"),
        ("accounts", "0005_user_authority"),
    ]

    operations = [
        migrations.AddField(
            model_name="authority",
            name="primary_contact",
            field=models.ForeignKey(
                blank=True,
                help_text="Designated contact person for this unit (must be a user assigned to this authority).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="primary_contact_for",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_authority_members, migrations.RunPython.noop),
        migrations.RemoveField(model_name="authority", name="designation"),
        migrations.RemoveField(model_name="authority", name="email"),
        migrations.RemoveField(model_name="authority", name="members"),
        migrations.RemoveField(model_name="authority", name="officer_name"),
        migrations.RemoveField(model_name="authority", name="phone"),
    ]
