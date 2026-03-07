from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_alter_coachathlete_coach"),
    ]

    operations = [
        migrations.AddField(
            model_name="coachathlete",
            name="focus",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="coachathlete",
            name="sort_order",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
    ]
