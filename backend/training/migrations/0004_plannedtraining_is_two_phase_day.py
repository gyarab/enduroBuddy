from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0003_alter_plannedtraining_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="plannedtraining",
            name="is_two_phase_day",
            field=models.BooleanField(default=False),
        ),
    ]
