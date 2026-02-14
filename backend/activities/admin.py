from django.contrib import admin
from django import forms

from .models import Activity, ActivityFile, ActivityInterval, ActivitySample
from .services.fit_importer import import_fit_into_activity


# Volitelné: inline intervaly v Activity adminu
class ActivityIntervalInline(admin.TabularInline):
    model = ActivityInterval
    extra = 0


# Volitelné: inline samples v Activity adminu (pozor: může být hodně řádků)
class ActivitySampleInline(admin.TabularInline):
    model = ActivitySample
    extra = 0


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "athlete", "sport", "workout_type", "started_at", "distance_m", "duration_s")
    search_fields = ("title", "athlete__username")
    list_filter = ("sport", "workout_type")
    inlines = [ActivityIntervalInline]  # sample inline radši nedávat, je to velké


class ActivityFileAdminForm(forms.ModelForm):
    file_upload = forms.FileField(required=False)

    class Meta:
        model = ActivityFile
        fields = ["activity", "file_type", "original_name"]  # file pole sem nedáváme


@admin.register(ActivityFile)
class ActivityFileAdmin(admin.ModelAdmin):
    form = ActivityFileAdminForm
    list_display = ("id", "activity", "file_type", "original_name", "uploaded_at")

    def save_model(self, request, obj: ActivityFile, form, change):
        uploaded = form.cleaned_data.get("file_upload")

        # pokud jen edituješ existující log záznam bez uploadu
        if not uploaded:
            return super().save_model(request, obj, form, change)

        # nastav original_name (ať projdou testy)
        if not obj.original_name:
            obj.original_name = uploaded.name

        # nikdy neukládej fyzický soubor do MEDIA
        obj.file = None

        # ulož log řádek ActivityFile
        super().save_model(request, obj, form, change)

        # import do DB (intervaly/samples/summary)
        import_fit_into_activity(
            activity=obj.activity,
            fileobj=uploaded.file,
            original_name=obj.original_name,
            create_activity_file_row=False,  # už máme log řádek (obj)
        )
