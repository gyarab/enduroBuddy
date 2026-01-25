from django.contrib import admin
from .models import Profile, CoachAthlete

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