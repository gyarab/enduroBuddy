from django.contrib import admin
from django.db import transaction

from .models import Activity, ActivityFile, ActivityInterval
from .services.fit_parser import parse_fit_file


class ActivityFileInline(admin.TabularInline):
    model = ActivityFile
    extra = 0
    fields = ("file_type", "original_name", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class ActivityIntervalInline(admin.TabularInline):
    model = ActivityInterval
    extra = 0
    fields = ("index", "duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km", "note")
    ordering = ("index",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "workout_type", "started_at", "distance_m", "duration_s", "avg_hr")
    list_filter = ("sport", "workout_type", "athlete")
    search_fields = ("title", "athlete__username")
    autocomplete_fields = ("athlete", "planned_training")
    inlines = [ActivityFileInline, ActivityIntervalInline]


@admin.action(description="Re-parse selected FIT files (overwrite summary + intervals)")
def reparse_fit_files(modeladmin, request, queryset):
    for af in queryset:
        if af.file_type != ActivityFile.FileType.FIT or not af.file:
            continue

        res = parse_fit_file(af.file.path)
        activity = af.activity

        with transaction.atomic():
            s = res.summary or {}

            activity.started_at = s.get("started_at") or activity.started_at
            activity.title = s.get("title") or activity.title
            activity.sport = s.get("sport") or activity.sport
            activity.workout_type = s.get("workout_type") or activity.workout_type

            activity.duration_s = s.get("duration_s")
            activity.distance_m = s.get("distance_m")
            activity.avg_hr = s.get("avg_hr")
            #activity.max_hr = s.get("max_hr")
            activity.avg_pace_s_per_km = s.get("avg_pace_s_per_km")
            activity.save()

            ActivityInterval.objects.filter(activity=activity).delete()

            rows = []
            for i, row in enumerate(res.intervals or [], start=1):
                rows.append(ActivityInterval(
                    activity=activity,
                    index=i,
                    duration_s=row.get("duration_s"),
                    distance_m=row.get("distance_m"),
                    avg_hr=row.get("avg_hr"),
                    #max_hr=row.get("max_hr"),
                    avg_pace_s_per_km=row.get("avg_pace_s_per_km"),
                    note=row.get("note", "") or "",
                ))
            if rows:
                ActivityInterval.objects.bulk_create(rows, batch_size=200)


@admin.register(ActivityFile)
class ActivityFileAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "file_type", "original_name", "uploaded_at")
    list_filter = ("file_type", "uploaded_at")
    search_fields = ("original_name", "activity__title", "activity__athlete__username")
    actions = [reparse_fit_files]


@admin.register(ActivityInterval)
class ActivityIntervalAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "index", "duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km", "note")
    list_filter = ("activity__athlete", "activity__sport")
    ordering = ("activity_id", "index")
