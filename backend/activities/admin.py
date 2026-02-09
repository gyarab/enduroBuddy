from django.contrib import admin
from .models import Activity, ActivityFile, ActivityInterval


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "workout_type", "started_at", "planned_training")
    list_filter = ("sport", "workout_type")
    search_fields = ("title", "athlete__username")
    autocomplete_fields = ("athlete", "planned_training")


@admin.register(ActivityFile)
class ActivityFileAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "file_type", "original_name", "uploaded_at")
    list_filter = ("file_type",)
    search_fields = ("original_name", "activity__athlete__username")


@admin.register(ActivityInterval)
class ActivityIntervalAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "index", "duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km")
    list_filter = ("activity__sport",)
