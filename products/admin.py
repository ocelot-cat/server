from django.contrib import admin
from .models import Product, ProductRecord


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductRecord)
class ProductRecordAdmin(admin.ModelAdmin):
    pass
