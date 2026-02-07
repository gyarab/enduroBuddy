from django.contrib import admin
from .models import Activity, Interval

class IntervalInline(admin.TabularInline):
    model = Interval
    extra = 0

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'athlete', 'sport', 'start_time', 'distance_m', 'duration', 'average_hr', 'max_hr', 'is_interval_session')
    list_filter = ('sport', 'is_interval_session', 'start_time')
    search_fields = ('athlete__username', 'source_file_name')

    inlines = [IntervalInline]