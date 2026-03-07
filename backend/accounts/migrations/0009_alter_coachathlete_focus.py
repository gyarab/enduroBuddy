from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_alter_coachathlete_focus"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE accounts_coachathlete
                SET focus = LEFT(focus, 30)
                WHERE LENGTH(focus) > 30;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="coachathlete",
            name="focus",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
    ]
