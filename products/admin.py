from django.contrib import admin

from companies.models import Notification
from .models import Product, ProductRecord


class ProductRecordInline(admin.TabularInline):
    model = ProductRecord
    extra = 0
    readonly_fields = ("record_date",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
    )
    search_fields = ("name", "category")
    list_filter = ("category",)
    inlines = [ProductRecordInline]


@admin.register(ProductRecord)
class ProductRecordAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "record_type",
        "piece_quantity",
        "recorded_by",
        "record_date",
    )
    list_filter = ("record_type", "record_date", "recorded_by")
    search_fields = ("product__name",)
    readonly_fields = ("record_date",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "recorded_by")


# Notification 모델
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
