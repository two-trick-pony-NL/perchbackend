import json
from django.contrib import admin
from django.utils.html import format_html

from ingestion.models import GPSBatch


@admin.register(GPSBatch)
class GPSBatchAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "start_time",
        "end_time",
        "point_count",
        "status",
        "attempts",
    )

    list_filter = (
        "status",
        "user",
        "start_time",
        "end_time",
    )

    search_fields = (
        "user__id",
        "user__email",
    )

    ordering = ("-start_time",)

    readonly_fields = (
        "user",
        "start_time",
        "end_time",
        "point_count",
        "points",
        "status",
        "attempts",
        "last_error",
        "created_at",
        "updated_at",
        "formatted_points",
    )

    fieldsets = (
        ("Meta", {
            "fields": (
                "user",
                "status",
                "attempts",
                "last_error",
                "point_count",
                "start_time",
                "end_time",
            )
        }),
        ("Data", {
            "fields": (
                "formatted_points",
            )
        }),
    )

    def formatted_points(self, obj):
        if not obj.points:
            return "-"

        pretty = json.dumps(obj.points, indent=2)

        return format_html(
            "<pre style='white-space: pre-wrap; font-size: 12px;'>{}</pre>",
            pretty
        )

    formatted_points.short_description = "Points (formatted)"

    def has_add_permission(self, request):
        return False  # created by ingestion pipeline only

    def has_delete_permission(self, request, obj=None):
        return True


    @admin.action(description="Mark selected as PENDING")
    def make_pending(modeladmin, request, queryset):
        queryset.update(status=GPSBatch.Status.PENDING, last_error=None)


    @admin.action(description="Mark selected as PROCESSING")
    def make_processing(modeladmin, request, queryset):
        queryset.update(status=GPSBatch.Status.PROCESSING)


    @admin.action(description="Mark selected as DONE")
    def make_done(modeladmin, request, queryset):
        queryset.update(status=GPSBatch.Status.DONE)


    @admin.action(description="Mark selected as FAILED")
    def make_failed(modeladmin, request, queryset):
        queryset.update(status=GPSBatch.Status.FAILED)

    actions = [
        make_pending,
        make_processing,
        make_done,
        make_failed,
    ]