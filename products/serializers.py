from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Product, ProductRecord


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
    # records = ProductRecordSerializer(many=True, read_only=True)  # 히스토리 내역
    current_stock = serializers.SerializerMethodField()  # 계산된 현재 재고

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "uuid",
            "category",
            "company",
            "storage_months",
            "pieces_per_box",
            "current_stock",  # 필요하면 추가
        ]

    def get_current_stock(self, obj):
        """현재 재고 계산"""
        return obj.get_total_stock()
