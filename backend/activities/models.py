from django.conf import settings
from django.db import models


class Activity(models.Model):
    class Sport(models.TextChoices):
        RUN = "RUN", "Run"
        BIKE = "BIKE", "Bike"
        SWIM = "SWIM", "Swim"
        OTHER = "OTHER", "Other"

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )

    sport = models.CharField(
        max_length=20,
        choices=Sport.choices,
        default=Sport.RUN,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)

    # agregované hodnoty (vyplní parser)
    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "no-date"
        return f"{self.athlete} | {self.sport} | {ts}"


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

    file = models.FileField(upload_to="activity_files/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.activity_id} | {self.file_type} | {self.original_name or self.file.name}"


class ActivityInterval(models.Model):
    """
    místo 'split' používáme 'interval'
    """
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="intervals",
    )

    index = models.PositiveIntegerField()  # 1..N

    # typicky intervaly z FIT: lapy / opakování
    duration_s = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_pace_s_per_km = models.PositiveIntegerField(null=True, blank=True)

    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["index"]
        unique_together = [("activity", "index")]

    def __str__(self):
        return f"Activity {self.activity_id} | Interval {self.index}"
