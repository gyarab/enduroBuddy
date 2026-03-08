from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_importjob"),
    ]

    operations = [
        migrations.AddField(
            model_name="importjob",
            name="total_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="importjob",
            name="processed_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]

