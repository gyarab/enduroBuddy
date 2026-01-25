from django.contrib import admin
from .models import TrainingMonth, TrainingWeek, PlannedTraining


@admin.register(TrainingMonth)
class TrainingMonthAdmin(admin.ModelAdmin):
    list_display = ("athlete", "month", "year")
    list_filter = ("year", "month")
    search_fields = ("athlete__username",)


@admin.register(TrainingWeek)
class TrainingWeekAdmin(admin.ModelAdmin):
    list_display = ("training_month", "week_index")
    list_filter = ("training_month__year", "training_month__month")


@admin.register(PlannedTraining)
class PlannedTrainingAdmin(admin.ModelAdmin):
    list_display = ("week", "day_label", "title", "planned_distance_km", "order_in_day")
    list_filter = ("week__training_month__year", "week__training_month__month", "day_label")
    search_fields = ("title", "week__training_month__athlete__username")
