from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_traininggroupinvite"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coachathlete",
            name="coach",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="coached_athletes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
