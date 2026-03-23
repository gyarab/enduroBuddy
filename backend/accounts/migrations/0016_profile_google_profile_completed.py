from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_appnotification"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="google_profile_completed",
            field=models.BooleanField(default=False),
        ),
    ]
