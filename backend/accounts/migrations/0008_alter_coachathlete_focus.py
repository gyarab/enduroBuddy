from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_coachathlete_focus_and_sort_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coachathlete",
            name="focus",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
    ]
