from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0006_alter_plannedtraining_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="plannedtraining",
            name="session_type",
            field=models.CharField(
                choices=[("RUN", "Run"), ("WORKOUT", "Workout")],
                default="RUN",
                max_length=10,
            ),
        ),
    ]

