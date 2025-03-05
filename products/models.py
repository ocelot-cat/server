from uuid import uuid4
from django.db import models, transaction
from django.db.models import F
from typing import List, Dict
from core.models import CommonModel
from users.models import User
from django.urls import reverse


class Product(CommonModel):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    category = models.CharField(max_length=50)
    piece_quantity = models.IntegerField(default=0)
    box_quantity = models.IntegerField(default=0)
    container_quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"uuid": self.uuid})

    def get_qr_code_url(self):
        return f"http://127.0.0.1:8000/api/v1/products/{self.uuid}"


class ProductRecord(models.Model):
    RECORD_TYPE_CHOICES = (
        ("in", "입고"),
        ("out", "출고"),
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="records"
    )
    record_type = models.CharField(max_length=3, choices=RECORD_TYPE_CHOICES)
    piece_quantity = models.IntegerField(default=0)
    box_quantity = models.IntegerField(default=0)
    container_quantity = models.IntegerField(default=0)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    record_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                multiplier = 1 if self.record_type == "in" else -1
                Product.objects.filter(id=self.product.id).update(
                    piece_quantity=F("piece_quantity")
                    + multiplier * self.piece_quantity,
                    box_quantity=F("box_quantity") + multiplier * self.box_quantity,
                    container_quantity=F("container_quantity")
                    + multiplier * self.container_quantity,
                )

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            multiplier = -1 if self.record_type == "in" else 1
            Product.objects.filter(id=self.product.id).update(
                piece_quantity=F("piece_quantity") + multiplier * self.piece_quantity,
                box_quantity=F("box_quantity") + multiplier * self.box_quantity,
                container_quantity=F("container_quantity")
                + multiplier * self.container_quantity,
            )
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.product.name}"


class ProductRecordManager:
    @staticmethod
    @transaction.atomic
    def bulk_create_records(records_data: List[Dict]) -> None:
        product_records = []
        product_updates = {}

        for data in records_data:
            product = data["product"]
            record_type = data["record_type"]
            piece_qty = data["piece_quantity"]
            box_qty = data["box_quantity"]
            container_qty = data["container_quantity"]

            product_records.append(
                ProductRecord(
                    product=product,
                    record_type=record_type,
                    piece_quantity=piece_qty,
                    box_quantity=box_qty,
                    container_quantity=container_qty,
                    recorded_by=data["user"],
                    note=data.get("note", ""),
                )
            )

            if product.id not in product_updates:
                product_updates[product.id] = {
                    "piece_quantity": 0,
                    "box_quantity": 0,
                    "container_quantity": 0,
                }

            multiplier = 1 if record_type == "in" else -1
            product_updates[product.id]["piece_quantity"] += multiplier * piece_qty
            product_updates[product.id]["box_quantity"] += multiplier * box_qty
            product_updates[product.id]["container_quantity"] += (
                multiplier * container_qty
            )

        # 벌크 생성
        ProductRecord.objects.bulk_create(product_records)

        # 벌크 업데이트
        for product_id, updates in product_updates.items():
            Product.objects.filter(id=product_id).update(
                piece_quantity=F("piece_quantity") + updates["piece_quantity"],
                box_quantity=F("box_quantity") + updates["box_quantity"],
                container_quantity=F("container_quantity")
                + updates["container_quantity"],
            )
