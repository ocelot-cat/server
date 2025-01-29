from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserInterest


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (
            "Profile",
            {
                "fields": (
                    "username",
                    "password",
                    "is_public",
                    "followings",
                ),
                "classes": ("wide",),
            },
        ),
    )


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ("user", "tag", "score")
    list_filter = ("user", "tag")
    search_fields = ("user__username", "tag__name")
    ordering = ("-score",)
