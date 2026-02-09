from django.conf import settings
from django.db import models


class Activity(models.Model):
    class Sport(models.TextChoices):
        RUN = "RUN", "Run"
        BIKE = "BIKE", "Bike"
        SWIM = "SWIM", "Swim"
        OTHER = "OTHER", "Other"

    class WorkoutType(models.TextChoices):
        RUN = "RUN", "Run (easy)"
        WORKOUT = "WORKOUT", "Workout"
        UNKNOWN = "UNKNOWN", "Unknown"

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )

    # Pro dashboard: Activity patří ke konkrétnímu PlannedTraining (volitelné)
    planned_training = models.OneToOneField(
        "training.PlannedTraining",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity",
    )

    sport = models.CharField(
        max_length=20,
        choices=Sport.choices,
        default=Sport.RUN,
    )

    workout_type = models.CharField(
        max_length=20,
        choices=WorkoutType.choices,
        default=WorkoutType.UNKNOWN,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)

    # agregované hodnoty (vyplní parser)
    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)  # <--- NOVÉ
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "no-date"
        return f"{self.athlete} | {self.sport} | {ts}"
        
    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"


class ActivityFile(models.Model):
    class FileType(models.TextChoices):
        FIT = "FIT", "FIT"
        GPX = "GPX", "GPX"
        TCX = "TCX", "TCX"
        OTHER = "OTHER", "OTHER"

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="files",
    )

    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
        default=FileType.FIT,
    )

    # aby šlo soubor po importu smazat a nechat jen metadata
    file = models.FileField(upload_to="activity_files/%Y/%m/", null=True, blank=True)
    original_name = models.CharField(max_length=255, blank=True)

    # volitelné: uložíme “raw” data (debug + budoucí Garmin API)
    raw_json = models.JSONField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.original_name or (self.file.name if self.file else "")
        return f"{self.activity_id} | {self.file_type} | {name}"


class ActivityLap(models.Model):
    """
    Raw 'laps' z FIT (auto-lap 1km, ruční lapy, workout step lapy... prostě vše).
    """
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="laps",
    )

    index = models.PositiveIntegerField()  # 1..N

    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)

    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)

    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["index"]
        unique_together = [("activity", "index")]

    def __str__(self):
        return f"Activity {self.activity_id} | Lap {self.index}"


class ActivityInterval(models.Model):
    """
    Dashboardové 'intervaly' (pracovní úseky) – u WORKOUT ukládáme jen work intervals (bez pauz).
    U RUN typicky prázdné.
    """
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="intervals",
    )

    index = models.PositiveIntegerField()  # 1..N

    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["index"]
        unique_together = [("activity", "index")]

    def __str__(self):
        return f"Activity {self.activity_id} | Interval {self.index}"


class ActivityRecord(models.Model):
    """
    Time-series (records) z FIT – základ pro budoucí grafy/statistiky.
    """
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="records",
    )

    ts = models.DateTimeField(null=True, blank=True)  # timestamp z FIT record

    # nejběžnější metriky
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    speed_mps = models.FloatField(null=True, blank=True)

    hr = models.PositiveSmallIntegerField(null=True, blank=True)
    cadence = models.PositiveSmallIntegerField(null=True, blank=True)

    altitude_m = models.FloatField(null=True, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["ts"]
        indexes = [
            models.Index(fields=["activity", "ts"]),
        ]

    def __str__(self):
        return f"Activity {self.activity_id} | Record {self.ts or 'no-ts'}"
