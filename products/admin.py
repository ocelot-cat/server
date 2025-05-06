from django import forms
from django.contrib import admin
from django.db.models import Avg
from django.forms import ModelForm
from django.utils import timezone
from django.utils.timezone import timedelta
from products.services import upload_image_to_cloudflare
from .models import Product, ProductImage, ProductRecord, ProductRecordSnapshot
from django.core.cache import cache


class ProductImageForm(ModelForm):
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


class ProductRecordSnapshotForm(ModelForm):
    class Meta:
        model = ProductRecordSnapshot
        fields = [
            "company",
            "product",
            "snapshot_date",
            "box_quantity",
            "piece_quantity",
        ]

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        product = cleaned_data.get("product")
        snapshot_date = cleaned_data.get("snapshot_date")

        if company and product and snapshot_date:
            if ProductRecordSnapshot.objects.filter(
                company=company, product=product, snapshot_date=snapshot_date
            ).exists():
                raise forms.ValidationError(
                    "해당 회사, 제품, 날짜에 대한 스냅샷이 이미 존재합니다."
                )

            if product.company != company:
                raise forms.ValidationError(
                    "선택한 제품은 해당 회사에 속해 있지 않습니다."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        product = instance.product

        total_pieces = (
            instance.box_quantity * product.pieces_per_box + instance.piece_quantity
        )
        instance.total_pieces = total_pieces

        if commit:
            instance.save()
            if cache.__class__.__module__.startswith("django_redis"):
                try:
                    cache.delete_pattern(f"products:company:{instance.company_id}:*")
                    cache.delete_pattern(
                        f"product_flow:company:{instance.company_id}:*"
                    )
                except Exception:
                    pass
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


@admin.register(ProductRecordSnapshot)
class ProductRecordSnapshotAdmin(admin.ModelAdmin):
    form = ProductRecordSnapshotForm
    list_display = (
        "company",
        "product",
        "snapshot_date",
        "box_quantity",
        "piece_quantity",
        "total_pieces",
        "created_at",
        "avg_last_30_days",
    )
    list_filter = ("snapshot_date", "company")
    search_fields = ("product__name", "company__name")
    readonly_fields = ("created_at", "total_pieces")
    date_hierarchy = "snapshot_date"
    raw_id_fields = ("company", "product")

    def avg_last_30_days(self, obj):
        last_month = timezone.now().date() - timedelta(days=30)
        thirty_days_ago = last_month - timedelta(days=30)
        avg_stock = (
            ProductRecordSnapshot.objects.filter(
                product=obj.product,
                snapshot_date__lte=last_month,
                snapshot_date__gte=thirty_days_ago,
            ).aggregate(avg_total_pieces=Avg("total_pieces"))
        )["avg_total_pieces"] or 0.0
        return round(avg_stock, 2)
