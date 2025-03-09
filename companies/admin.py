from django.contrib import admin
from .models import Company, Department, Invitation, CompanyMembership


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
