from django.contrib import admin
from .models import Activity, ActivityInterval

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "started_at")

@admin.register(ActivityInterval)
class ActivityIntervalAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "index", "duration_s", "distance_m")
