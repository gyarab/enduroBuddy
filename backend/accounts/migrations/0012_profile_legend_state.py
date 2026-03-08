from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_coachathlete_hidden_from_plans"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="legend_state",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

