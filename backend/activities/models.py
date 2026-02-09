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

    planned_training = models.OneToOneField(
        "training.PlannedTraining",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity",
    )

    sport = models.CharField(max_length=20, choices=Sport.choices, default=Sport.RUN)
    workout_type = models.CharField(max_length=20, choices=WorkoutType.choices, default=WorkoutType.UNKNOWN)

    started_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)

    # minimum pro dashboard
    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    #max_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self):
        ts = self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "no-date"
        return f"{self.athlete} | {self.sport} | {ts}"


class ActivityFile(models.Model):
    class FileType(models.TextChoices):
        FIT = "FIT", "FIT"
        GPX = "GPX", "GPX"
        TCX = "TCX", "TCX"
        OTHER = "OTHER", "OTHER"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="files")
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.FIT)

    # MVP: soubor se vždy uloží do media
    file = models.FileField(upload_to="activity_files/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.original_name or (self.file.name if self.file else "")
        return f"{self.activity_id} | {self.file_type} | {name}"


class ActivityInterval(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="intervals")
    index = models.PositiveIntegerField()  # 1..N

    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    #max_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["index"]
        unique_together = [("activity", "index")]

    def __str__(self):
        return f"Activity {self.activity_id} | Interval {self.index}"
