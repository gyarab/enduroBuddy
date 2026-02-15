from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0004_plannedtraining_is_two_phase_day"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="trainingmonth",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="trainingweek",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="trainingmonth",
            constraint=models.UniqueConstraint(
                fields=("athlete", "year", "month"),
                name="uniq_training_month_athlete_year_month",
            ),
        ),
        migrations.AddConstraint(
            model_name="trainingweek",
            constraint=models.UniqueConstraint(
                fields=("training_month", "week_index"),
                name="uniq_training_week_month_index",
            ),
        ),
        migrations.AddIndex(
            model_name="plannedtraining",
            index=models.Index(
                fields=["week", "date", "order_in_day"],
                name="trn_week_date_order_idx",
            ),
        ),
    ]
