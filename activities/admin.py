from django.contrib import admin

from activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_filter = (
        "actor",
        "recipient",
        "post",
        "activity_type",
        "is_read",
    )
