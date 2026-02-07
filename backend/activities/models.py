from django.db import models
from django.conf import settings

class Activity(models.Model):
    class Sport(models.TextChoices):
        RUN = 'run', 'Run'
        BIKE = 'bike', 'Bike'
        SWIM = 'swim', 'Swim'
        OTHER = 'other', 'Other'

    athlete = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    sport = models.CharField(max_length=20, choices=Sport.choices, default=Sport.RUN)

    start_time = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(default=0)  # Duration in seconds
    distance_m = models.PositiveIntegerField(default=0)  # Distance in meters
    average_hr = models.PositiveIntegerField(null=True, blank=True)  # Average heart rate
    max_hr = models.PositiveIntegerField(null=True, blank=True)  # Max heart rate

    is_interval_session = models.BooleanField(default=False)

    athlete_note = models.TextField(blank=True)

    source_file_name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.start_time.strftime('%Y-%m-%d %H:%M') if self.start_time else 'no-time'
        return f'{self.athlete} | {self.sport} | {ts}'
    
class Interval(models.Model):
    activity = models.ForeignKey(Activity,on_delete=models.CASCADE,related_name="intervals")

    label = models.CharField(max_length=80, blank=True)

    time_s = models.PositiveIntegerField(default=0)
    distance_m = models.PositiveIntegerField(default=0)

    avg_hr = models.PositiveIntegerField(null=True, blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.activity_id} interval {self.order}"