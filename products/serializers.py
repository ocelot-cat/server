import tempfile
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers
from companies.models import Company
from .tasks import upload_image_to_cloudflare_task
from .models import Product, ProductImage, ProductRecord
import logging

logger = logging.getLogger(__name__)


class ProductSerializer(serializers.ModelSerializer):
    current_stock = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    image_urls = serializers.SerializerMethodField(read_only=True)
    image_upload_status = serializers.CharField(read_only=True)
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
            "image_urls",
            "image_upload_status",
            "current_stock",
        ]

    def get_current_stock(self, obj):
        return obj.get_total_stock()

    def get_image_urls(self, obj):
        return [image.image_url for image in obj.images.all()]

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
        logger.info(f"Received {len(images_data)} images for product creation via API")
        product = Product.objects.create(**validated_data)

        for image_file in images_data:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ) as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                logger.info(
                    f"Scheduling image upload task for product {product.id} with file {temp_file_path}, content_type: {image_file.content_type}"
                )
                upload_image_to_cloudflare_task.delay(
                    temp_file_path, product.id, content_type=image_file.content_type
                )
                ProductImage.objects.create(
                    product=product,
                    image_url="https://imagedelivery.net/BxK0jiFZvOFWaDu7QtKNcQ/pending/public",
                )
            except Exception as e:
                logger.error(
                    f"Failed to schedule image upload for product {product.id}: {str(e)}"
                )
                product.image_upload_status = "failed"
                ProductImage.objects.create(
                    product=product,
                    image_url="https://imagedelivery.net/BxK0jiFZvOFWaDu7QtKNcQ/default/public",
                )
                product.save()

        return product


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
