from django.db import migrations, models


def sync_builtin_permissions(apps, schema_editor):
    from rbac.features import APP_FEATURES

    Permission = apps.get_model("rbac", "Permission")
    for index, feature in enumerate(APP_FEATURES):
        Permission.objects.update_or_create(
            codename=feature.codename,
            defaults={
                "name": feature.name,
                "is_builtin": True,
                "show_in_menu": feature.show_in_menu,
                "menu_label": feature.menu_label,
                "menu_icon": feature.menu_icon,
                "menu_section": feature.menu_section,
                "url_name": feature.url_name,
                "sort_order": index,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0004_simplify_permission_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="permission",
            name="is_builtin",
            field=models.BooleanField(
                default=False,
                help_text="Synced from application code; cannot be deleted.",
            ),
        ),
        migrations.AddField(
            model_name="permission",
            name="menu_icon",
            field=models.CharField(blank=True, default="fa-circle", max_length=50),
        ),
        migrations.AddField(
            model_name="permission",
            name="menu_label",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="permission",
            name="menu_section",
            field=models.CharField(
                choices=[("menu", "Menu"), ("admin", "Administration")],
                default="menu",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="permission",
            name="show_in_menu",
            field=models.BooleanField(
                default=False,
                help_text="Show a sidebar link for users who have this permission.",
            ),
        ),
        migrations.AddField(
            model_name="permission",
            name="sort_order",
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name="permission",
            name="url_name",
            field=models.CharField(
                blank=True,
                help_text="Django URL name, e.g. portal:dashboard",
                max_length=200,
            ),
        ),
        migrations.AlterModelOptions(
            name="permission",
            options={"ordering": ["sort_order", "name"]},
        ),
        migrations.RunPython(sync_builtin_permissions, migrations.RunPython.noop),
    ]
