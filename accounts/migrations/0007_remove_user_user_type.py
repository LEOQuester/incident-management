from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_remove_user_authority"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="user_type",
        ),
    ]
