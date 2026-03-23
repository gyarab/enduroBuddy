from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0016_profile_google_profile_completed"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="google_role_confirmed",
            field=models.BooleanField(default=False),
        ),
    ]
