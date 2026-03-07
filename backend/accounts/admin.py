from django.contrib import admin
from .models import (
    CoachAthlete,
    CoachJoinRequest,
    GarminConnection,
    GarminSyncAudit,
    Profile,
    TrainingGroup,
    TrainingGroupAthlete,
    TrainingGroupInvite,
)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(CoachAthlete)
class CoachAthleteAdmin(admin.ModelAdmin):
    list_display = ('coach', 'athlete', 'hidden_from_plans', 'created_at')
    list_filter = ('hidden_from_plans', 'created_at',)
    search_fields = ('coach__username', 'athlete__username')


@admin.register(CoachJoinRequest)
class CoachJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("coach", "athlete", "status", "created_at", "decided_at")
    list_filter = ("status", "created_at", "decided_at")
    search_fields = ("coach__username", "athlete__username", "coach__email", "athlete__email")


@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "coach", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "coach__username", "coach__email")


@admin.register(TrainingGroupAthlete)
class TrainingGroupAthleteAdmin(admin.ModelAdmin):
    list_display = ("group", "athlete", "created_at")
    list_filter = ("created_at",)
    search_fields = ("group__name", "athlete__username", "athlete__email")


@admin.register(TrainingGroupInvite)
class TrainingGroupInviteAdmin(admin.ModelAdmin):
    list_display = ("group", "created_by", "invited_email", "expires_at", "used_at", "used_by")
    list_filter = ("created_at", "expires_at", "used_at")
    search_fields = ("group__name", "created_by__username", "invited_email", "token")
    readonly_fields = ("created_at",)


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
