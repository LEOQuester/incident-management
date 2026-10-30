from django.db import migrations, models
import django.db.models.deletion


def migrate_user_authority_to_unit_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("rbac", "Role")
    Authority = apps.get_model("incidents", "Authority")
    Permission = apps.get_model("rbac", "Permission")

    update_cases = Permission.objects.filter(codename="update_cases").first()
    view_profile = Permission.objects.filter(codename="view_profile").first()
    view_dashboard = Permission.objects.filter(codename="view_dashboard").first()
    base_perms = [p for p in (view_profile, view_dashboard, update_cases) if p]

    for authority in Authority.objects.all():
        role_name = f"{authority.name} staff"
        role, _ = Role.objects.get_or_create(
            name=role_name,
            defaults={"is_end_user_role": False},
        )
        role.authority_id = authority.pk
        role.save(update_fields=["authority_id"])
        if base_perms:
            role.permissions.add(*base_perms)

    for user in User.objects.filter(authority_id__isnull=False).iterator():
        role = Role.objects.filter(authority_id=user.authority_id).first()
        if role:
            user.roles.add(role)


class Migration(migrations.Migration):
    dependencies = [
        ("incidents", "0005_authority_primary_contact"),
        ("rbac", "0005_permission_menu_and_builtin"),
        ("accounts", "0005_user_authority"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="authority",
            field=models.ForeignKey(
                blank=True,
                help_text="When set, users with this role handle cases assigned to this authority unit.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="unit_roles",
                to="incidents.authority",
            ),
        ),
        migrations.RunPython(migrate_user_authority_to_unit_roles, migrations.RunPython.noop),
    ]
