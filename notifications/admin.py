from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "notification_type",
        "message",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("message", "user__username")
    ordering = ("-created_at",)
    list_per_page = 25

    readonly_fields = ("created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": ("user", "notification_type", "message", "related_object_id"),
            },
        ),
        (
            "상태",
            {
                "fields": ("is_read", "created_at"),
            },
        ),
    )
