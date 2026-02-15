from django.contrib import admin
from .models import CoachAthlete, GarminConnection, GarminSyncAudit, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(CoachAthlete)
class CoachAthleteAdmin(admin.ModelAdmin):
    list_display = ('coach', 'athlete', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('coach__username', 'athlete__username')


@admin.register(GarminConnection)
class GarminConnectionAdmin(admin.ModelAdmin):
    list_display = ("user", "garmin_email", "garmin_display_name", "is_active", "last_sync_at", "updated_at")
    list_filter = ("is_active", "updated_at")
    search_fields = ("user__username", "user__email", "garmin_email", "garmin_display_name")
    readonly_fields = ("connected_at", "updated_at", "last_sync_at", "revoked_at")


@admin.register(GarminSyncAudit)
class GarminSyncAuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "status", "window", "imported_count", "skipped_count")
    list_filter = ("action", "status", "window", "created_at")
    search_fields = ("user__username", "message")
    readonly_fields = ("created_at",)
