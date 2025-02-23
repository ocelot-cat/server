from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Company, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass
