from django.contrib import admin
from .models import Company, Department, Invitation, CompanyMembership, Notification


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "member_count")
    search_fields = ("name", "owner__username")
    list_filter = ("owner",)

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "회원 수"


@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = ("company", "user", "role")
    list_filter = ("company", "role")
    search_fields = ("company__name", "user__username")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("company", "user")
        return ()


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "company")
    list_filter = ("company",)
    search_fields = ("name", "company__name")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "email",
        "token",
        "expiration_date",
        "is_accepted",
        "is_used",
    )
    list_filter = ("company", "is_accepted", "is_used")
    search_fields = ("email", "company__name")
    readonly_fields = ("token",)
    date_hierarchy = "expiration_date"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("company", "email")
        return self.readonly_fields


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "company", "message", "is_read", "created_at")
    list_filter = ("is_read", "company")
    search_fields = ("recipient__username", "message", "company__name")
    raw_id_fields = ("recipient", "company")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(
                company__in=request.user.companies.filter(
                    companymembership__role__in=["admin", "owner"]
                )
            )
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
