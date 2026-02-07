from django.contrib import admin
from .models import Activity, ActivityInterval, ActivityFile


class ActivityIntervalInline(admin.TabularInline):
    model = ActivityInterval
    extra = 0


class ActivityFileInline(admin.TabularInline):
    model = ActivityFile
    extra = 0


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "started_at")
    inlines = [ActivityFileInline, ActivityIntervalInline]


@admin.register(ActivityInterval)
class ActivityIntervalAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "index", "duration_s", "distance_m")


@admin.register(ActivityFile)
class ActivityFileAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "file_type", "uploaded_at")
