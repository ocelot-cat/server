from django import forms
from django.contrib import admin

from companies.models import Notification
from products.services import upload_image_to_cloudflare
from .models import Product, ProductImage, ProductRecord


class ProductImageForm(forms.ModelForm):
    image_file = forms.ImageField(required=False, label="Upload Image")

    class Meta:
        model = ProductImage
        fields = ["image_url"]

    def clean(self):
        cleaned_data = super().clean()
        image_file = cleaned_data.get("image_file")
        image_url = cleaned_data.get("image_url")

        if not image_file and not image_url:
            return cleaned_data

        if image_file:
            cleaned_data["image_url"] = None
        elif not image_url:
            raise forms.ValidationError(
                "Please provide an image URL if no image file is uploaded."
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("image_file"):
            instance.image_url = upload_image_to_cloudflare(
                self.cleaned_data["image_file"]
            )
        if commit:
            instance.save()
        return instance


class ProductRecordInline(admin.TabularInline):
    model = ProductRecord
    extra = 0
    readonly_fields = ("record_date",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageForm
    extra = 1
    fields = ["image_file", "image_url"]
    readonly_fields = ["image_url"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
    )
    search_fields = ("name", "category")
    list_filter = ("category",)
    inlines = [ProductRecordInline, ProductImageInline]


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
