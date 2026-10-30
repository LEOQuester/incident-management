from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_department_user_user_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True,
                help_text="Profile photo (JPEG, PNG, or WebP, max 2 MB).",
                null=True,
                upload_to="avatars/",
            ),
        ),
    ]
