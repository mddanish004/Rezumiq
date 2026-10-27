from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_name_user_username_changed_at_usernameredirect"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="clerk_id",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar_url",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
    ]
