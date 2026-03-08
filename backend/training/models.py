from django.conf import settings
from django.db import models


class TrainingMonth(models.Model):
    athlete = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="training_months")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["athlete", "year", "month"], name="uniq_training_month_athlete_year_month"),
        ]
        ordering = ["-year", "-month"]
        verbose_name = "Training Month"
        verbose_name_plural = "Training Months"

    def __str__(self):
        return f"{self.athlete}: {self.month}/{self.year}"


class TrainingWeek(models.Model):
    training_month = models.ForeignKey(TrainingMonth, on_delete=models.CASCADE, related_name="weeks")
    week_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["training_month", "week_index"], name="uniq_training_week_month_index"),
        ]
        ordering = ["week_index"]
        verbose_name = "Training Week"
        verbose_name_plural = "Training Weeks"

    def __str__(self):
        return f"Week {self.week_index} | {self.training_month}"


class PlannedTraining(models.Model):
    class SessionType(models.TextChoices):
        RUN = "RUN", "Run"
        WORKOUT = "WORKOUT", "Workout"

    week = models.ForeignKey(TrainingWeek, on_delete=models.CASCADE, related_name="planned_trainings")
    date = models.DateField(null=True, blank=True)
    day_label = models.CharField(max_length=20)
    title = models.TextField(blank=True, default="")
    session_type = models.CharField(
        max_length=10,
        choices=SessionType.choices,
        default=SessionType.RUN,
    )
    planned_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    order_in_day = models.PositiveIntegerField(default=1)
    is_two_phase_day = models.BooleanField(default=False)

    class Meta:
        ordering = ("week__week_index", "date", "order_in_day")
        indexes = [
            models.Index(fields=["week", "date", "order_in_day"], name="trn_week_date_order_idx"),
        ]
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
    activity = models.OneToOneField(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_training",
    )
    time_seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveIntegerField(null=True, blank=True)
    feel = models.CharField(max_length=50, blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Completed: {self.planned}"
