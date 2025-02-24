from django.contrib import admin
from .models import Product, ProductRecord


class ProductRecordInline(admin.TabularInline):
    model = ProductRecord
    extra = 0
    readonly_fields = ("record_date",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "uuid",
        "category",
        "piece_quantity",
        "box_quantity",
        "container_quantity",
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
        "box_quantity",
        "container_quantity",
        "recorded_by",
        "record_date",
    )
    list_filter = ("record_type", "record_date", "recorded_by")
    search_fields = ("product__name",)
    readonly_fields = ("record_date",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "recorded_by")
