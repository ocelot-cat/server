from django.db import models, transaction
from django.core.validators import MinValueValidator
from companies.models import Company
from core.models import CommonModel
from users.models import User
from django.urls import reverse


class Product(CommonModel):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="products"
    )
    storage_months = models.IntegerField(
        default=6, validators=[MinValueValidator(1)], help_text="보관 가능 개월 수"
    )
    pieces_per_box = models.IntegerField(
        default=20, validators=[MinValueValidator(1)], help_text="한 박스당 개수"
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from companies.tasks import create_notification_for_new_product

            create_notification_for_new_product.delay(self.company_id, self.id)

    class Meta:
        indexes = [
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.id})

    def get_qr_code_url(self):
        return f"http://127.0.0.1:8000/api/v1/products/{self.id}"

    def get_total_stock(self):
        """현재 총 재고 계산"""
        records = self.records.filter(record_type="in")
        total_pieces = sum(
            (r.box_quantity * self.pieces_per_box)
            + r.piece_quantity
            - r.consumed_quantity
            for r in records
        )
        return {
            "box_quantity": total_pieces // self.pieces_per_box,
            "piece_quantity": total_pieces % self.pieces_per_box,
            "total_pieces": total_pieces,
        }


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
    consumed_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )  # 소진된 수량
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    record_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["record_date"]),
            models.Index(fields=["record_type"]),
            models.Index(fields=["expiration_date"]),
        ]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new and self.record_type == "out":
                self._consume_stock()

    def _consume_stock(self):
        """출고 시 FIFO로 재고 소진"""
        total_out_pieces = (
            self.box_quantity * self.product.pieces_per_box
        ) + self.piece_quantity
        if total_out_pieces <= 0:
            return

        # 입고 기록을 오래된 순으로 정렬
        in_records = self.product.records.filter(record_type="in").order_by(
            "record_date"
        )

        remaining_out = total_out_pieces
        for in_record in in_records:
            available_pieces = (
                (in_record.box_quantity * self.product.pieces_per_box)
                + in_record.piece_quantity
                - in_record.consumed_quantity
            )
            if available_pieces <= 0:
                continue

            consumed = min(available_pieces, remaining_out)
            in_record.consumed_quantity += consumed
            in_record.save(update_fields=["consumed_quantity"])
            remaining_out -= consumed

            if remaining_out <= 0:
                break

        if remaining_out > 0:
            raise ValueError("소진할 재고가 부족합니다.")

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.product.name}"
