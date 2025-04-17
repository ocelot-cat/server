from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers

from companies.models import Company
from .models import Product, ProductImage, ProductRecord


class ProductRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRecord
        fields = [
            "id",
            "product",
            "record_type",
            "piece_quantity",
            "box_quantity",
            "recorded_by",
            "record_date",
            "expiration_date",
            "consumed_quantity",
        ]
        read_only_fields = ["id", "record_date", "expiration_date", "consumed_quantity"]

    def validate(self, data):
        if data["record_type"] not in dict(ProductRecord.RECORD_TYPE_CHOICES):
            raise serializers.ValidationError(
                {"record_type": "유효하지 않은 기록 유형입니다."}
            )
        if data["piece_quantity"] < 0 or data["box_quantity"] < 0:
            raise serializers.ValidationError(
                {"quantity": "수량은 음수가 될 수 없습니다."}
            )
        return data

    def create(self, validated_data):
        validated_data["record_date"] = timezone.now()
        record = ProductRecord(**validated_data)
        if record.record_type == "in":
            record.expiration_date = record.record_date + relativedelta(
                months=record.product.storage_months
            )
        record.save()
        return record


class ProductSerializer(serializers.ModelSerializer):
    current_stock = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "company",
            "storage_months",
            "pieces_per_box",
            "unit",
            "quantity",
            "images",
            "current_stock",
        ]

    def get_current_stock(self, obj):
        return obj.get_total_stock()

    def validate(self, data):
        unit = data.get("unit")
        quantity = data.get("quantity")
        if unit != "count" and (quantity is None or quantity < 0):
            raise serializers.ValidationError(
                {"quantity": "단위가 'count'가 아닌 경우 수량은 0 이상이어야 합니다."}
            )
        if unit == "count" and quantity is not None and quantity != 1:
            raise serializers.ValidationError(
                {"quantity": "단위가 'count'인 경우 수량은 1이어야 합니다."}
            )
        return data

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        product = Product.objects.create(**validated_data)

        for image_url in images_data:
            ProductImage.objects.create(product=product, image_url=image_url)

        return product


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image_url"]
