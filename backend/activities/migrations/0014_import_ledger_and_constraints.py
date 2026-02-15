from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0013_activityfile_checksum_sha256"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityImportLedger",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checksum_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "athlete",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activity_import_ledgers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="activityinterval",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="activityinterval",
            constraint=models.UniqueConstraint(fields=("activity", "index"), name="uniq_activity_interval_index"),
        ),
        migrations.AddConstraint(
            model_name="activityimportledger",
            constraint=models.UniqueConstraint(
                fields=("athlete", "checksum_sha256"),
                name="uniq_import_ledger_athlete_checksum",
            ),
        ),
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(fields=["athlete", "started_at"], name="act_athlete_started_idx"),
        ),
        migrations.AddIndex(
            model_name="activityfile",
            index=models.Index(fields=["activity", "checksum_sha256"], name="actfile_activity_checksum_idx"),
        ),
        migrations.AddIndex(
            model_name="activityimportledger",
            index=models.Index(fields=["athlete", "created_at"], name="actledger_athlete_created_idx"),
        ),
    ]
