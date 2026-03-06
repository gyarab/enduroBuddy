from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0005_training_constraints_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plannedtraining",
            name="title",
            field=models.TextField(blank=True, default=""),
        ),
    ]
