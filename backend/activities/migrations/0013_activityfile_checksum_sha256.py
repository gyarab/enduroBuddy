from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0012_activity_max_hr_activityinterval_max_hr"),
    ]

    operations = [
        migrations.AddField(
            model_name="activityfile",
            name="checksum_sha256",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
    ]
