from uuid import uuid4
from django.db import models, transaction
from django.db.models import Case, When, F, IntegerField
from django.core.validators import MinValueValidator
from typing import List, Dict
from companies.models import Company
from core.models import CommonModel
from users.models import User
from django.urls import reverse


class Product(CommonModel):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    category = models.CharField(max_length=50)
    piece_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    box_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    container_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="products"
    )

    class Meta:
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["category"]),
        ]

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
    piece_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    box_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    container_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    record_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["record_date"]),
            models.Index(fields=["record_type"]),
        ]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                multiplier = 1 if self.record_type == "in" else -1
                Product.objects.select_for_update().filter(id=self.product.id).update(
                    piece_quantity=F("piece_quantity")
                    + multiplier * self.piece_quantity,
                    box_quantity=F("box_quantity") + multiplier * self.box_quantity,
                    container_quantity=F("container_quantity")
                    + multiplier * self.container_quantity,
                    version=F("version") + 1,
                )

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            multiplier = -1 if self.record_type == "in" else 1
            Product.objects.select_for_update().filter(id=self.product.id).update(
                piece_quantity=F("piece_quantity") + multiplier * self.piece_quantity,
                box_quantity=F("box_quantity") + multiplier * self.box_quantity,
                container_quantity=F("container_quantity")
                + multiplier * self.container_quantity,
                version=F("version") + 1,
            )
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.product.name}"


# 제품 기록 매니저
class ProductRecordManager:
    @staticmethod
    @transaction.atomic
    def bulk_create_records(records_data: List[Dict]) -> None:
        product_records = []
        product_ids = set()

        for data in records_data:
            product = data["product"]
            product_ids.add(product.id)
            product_records.append(
                ProductRecord(
                    product=product,
                    record_type=data["record_type"],
                    piece_quantity=data["piece_quantity"],
                    box_quantity=data["box_quantity"],
                    container_quantity=data["container_quantity"],
                    recorded_by=data["user"],
                    note=data.get("note", ""),
                )
            )

        ProductRecord.objects.bulk_create(product_records)

        Product.objects.select_for_update().filter(id__in=product_ids).update(
            piece_quantity=F("piece_quantity")
            + Case(
                *[
                    When(
                        id=pid,
                        then=sum(
                            r["piece_quantity"]
                            * (1 if r["record_type"] == "in" else -1)
                            for r in records_data
                            if r["product"].id == pid
                        ),
                    )
                    for pid in product_ids
                ],
                output_field=IntegerField(),
            ),
            box_quantity=F("box_quantity")
            + Case(
                *[
                    When(
                        id=pid,
                        then=sum(
                            r["box_quantity"] * (1 if r["record_type"] == "in" else -1)
                            for r in records_data
                            if r["product"].id == pid
                        ),
                    )
                    for pid in product_ids
                ],
                output_field=IntegerField(),
            ),
            container_quantity=F("container_quantity")
            + Case(
                *[
                    When(
                        id=pid,
                        then=sum(
                            r["container_quantity"]
                            * (1 if r["record_type"] == "in" else -1)
                            for r in records_data
                            if r["product"].id == pid
                        ),
                    )
                    for pid in product_ids
                ],
                output_field=IntegerField(),
            ),
            version=F("version") + 1,
        )
