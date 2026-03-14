from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_importjob_progress_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("COACH_JOIN_REQUEST", "Coach join request"), ("PLAN_UPDATED", "Plan updated"), ("COACH_NOTE", "Coach note")], db_index=True, max_length=40)),
                ("tone", models.CharField(choices=[("success", "Success"), ("info", "Info"), ("warning", "Warning"), ("danger", "Danger"), ("secondary", "Secondary")], default="info", max_length=16)),
                ("text", models.CharField(max_length=255)),
                ("dedupe_key", models.CharField(blank=True, db_index=True, default="", max_length=120)),
                ("read_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="triggered_app_notifications", to=settings.AUTH_USER_MODEL)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="app_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at", "-id"],
                "indexes": [models.Index(fields=["recipient", "read_at", "-created_at"], name="appnotif_rec_read_idx")],
            },
        ),
    ]
