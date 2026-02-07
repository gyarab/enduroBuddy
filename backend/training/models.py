from django.db import models
from django.conf import settings

class TrainingMonth(models.Model):
    athlete = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="training_months")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()

    class Meta:
        unique_together = ("athlete", "year", "month")
        ordering = ["-year", "-month"]
        verbose_name = "Training Month"
        verbose_name_plural = "Training Months"

    def __str__(self):
        return f"{self.athlete}: {self.month}/{self.year}"


class TrainingWeek(models.Model):
    training_month = models.ForeignKey(TrainingMonth, on_delete=models.CASCADE, related_name="weeks")
    week_index = models.PositiveIntegerField()

    class Meta:
        unique_together = ("training_month", "week_index")
        ordering = ["week_index"]
        verbose_name = "Training Week"
        verbose_name_plural = "Training Weeks"

    def __str__(self):
        return f"Week {self.week_index} | {self.training_month}"


class PlannedTraining(models.Model):
    week = models.ForeignKey(TrainingWeek, on_delete=models.CASCADE, related_name="planned_trainings")

    # ⚠️ doporučuji přidat datum (jinak se to bude párovat blbě)
    date = models.DateField(null=True, blank=True)

    day_label = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    planned_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    order_in_day = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("week__week_index", "date", "order_in_day")
        verbose_name = "Planned training"
        verbose_name_plural = "Planned trainings"

    def __str__(self):
        return f"{self.day_label}: {self.title}"


class CompletedTraining(models.Model):
    planned = models.OneToOneField(
        PlannedTraining,
        on_delete=models.CASCADE,
        related_name="completed",
    )

    # ✅ VARIANTA B: CompletedTraining → Activity
    activity = models.OneToOneField(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_training",
    )

    # jednoduché MVP – souhrn
    time_seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveIntegerField(null=True, blank=True)
    feel = models.CharField(max_length=50, blank=True, default="")
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Completed: {self.planned}"
