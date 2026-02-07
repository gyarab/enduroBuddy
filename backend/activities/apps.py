from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activities"

    def ready(self):
        # načtení signálů (musí být až tady)
        from . import signals  # noqa
