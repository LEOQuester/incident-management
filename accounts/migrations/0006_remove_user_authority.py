from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_user_authority"),
        ("rbac", "0006_role_authority"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="authority",
        ),
    ]
