from django.contrib import admin
from django.db import transaction

from .models import Activity, ActivityFile, ActivityInterval
from .services.fit_parser import parse_fit_file  # musí existovat


class ActivityFileInline(admin.TabularInline):
    model = ActivityFile
    extra = 0
    fields = ("file_type", "original_name", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class ActivityIntervalInline(admin.TabularInline):
    model = ActivityInterval
    extra = 0
    fields = ("index", "duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km", "note")
    readonly_fields = ()
    ordering = ("index",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "workout_type", "started_at", "distance_m", "duration_s")
    list_filter = ("sport", "workout_type", "athlete")
    search_fields = ("title", "athlete__username")
    inlines = [ActivityFileInline, ActivityIntervalInline]


@admin.action(description="Re-parse selected FIT files (overwrite intervals)")
def reparse_fit_files(modeladmin, request, queryset):
    """
    Manuální import: smaže existující intervaly a znovu je vytvoří z FIT.
    """
    for af in queryset:
        if af.file_type != ActivityFile.FileType.FIT:
            continue

        activity = af.activity
        if not af.file:
            continue

        with transaction.atomic():
            # smaž intervaly
            ActivityInterval.objects.filter(activity=activity).delete()

            # znovu parse + vytvoř intervaly
            intervals = parse_fit_file(af.file.path)

            for i, row in enumerate(intervals, start=1):
                ActivityInterval.objects.create(
                    activity=activity,
                    index=i,
                    duration_s=row.get("duration_s"),
                    distance_m=row.get("distance_m"),
                    avg_hr=row.get("avg_hr"),
                    avg_pace_s_per_km=row.get("avg_pace_s_per_km"),
                    note=row.get("note", ""),
                )


@admin.register(ActivityFile)
class ActivityFileAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "file_type", "original_name", "uploaded_at")
    list_filter = ("file_type", "uploaded_at")
    search_fields = ("original_name", "activity__title", "activity__athlete__username")
    actions = [reparse_fit_files]


@admin.register(ActivityInterval)
class ActivityIntervalAdmin(admin.ModelAdmin):
    list_display = ("id", "activity", "index", "duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km")
    list_filter = ("activity__athlete",)
    ordering = ("activity_id", "index")
