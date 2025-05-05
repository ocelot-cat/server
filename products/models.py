from django.db import models, transaction
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils import timezone
from companies.models import Company
from core.models import CommonModel
from users.models import User
from django.db.transaction import on_commit
from django.urls import reverse
from django.core.cache import cache


class Product(CommonModel):
    UNIT_CHOICES = (
        ("ml", "밀리리터(ml)"),
        ("g", "그램(g)"),
        ("kg", "킬로그램(kg)"),
        ("per", "매(장)"),
        ("count", "갯수"),
    )

    CATEGORY_CHOICES = (
        ("electronics", "전자제품"),
        ("fashion", "의류"),
        ("food", "식품"),
        ("household", "생활용품/가구"),
        ("chemicals", "화학/위험물"),
        ("pharma", "의약품"),
        ("raw_materials", "원자재"),
        ("miscellaneous", "기타"),
    )

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="products"
    )
    storage_months = models.IntegerField(
        default=6, validators=[MinValueValidator(1)], help_text="보관 가능 개월 수"
    )
    pieces_per_box = models.IntegerField(
        default=20, validators=[MinValueValidator(1)], help_text="한 박스당 개수"
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="count")
    quantity = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="단위에 따른 수량 (갯수는 입력 불필요)",
    )
    image_upload_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        help_text="Image upload status",
    )
    current_stock = models.IntegerField(default=0, help_text="현재 재고 (total_pieces)")
    avg_last_30_days_stock = models.FloatField(
        default=0.0, help_text="지난 30일 평균 재고 (total_pieces)"
    )
    variation = models.FloatField(
        default=0.0, help_text="지난 30일 평균 대비 변동률 (%)"
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if self.unit == "count":
            self.quantity = 1
        super().save(*args, **kwargs)
        if is_new:
            from companies.tasks import create_notification_for_new_product

            on_commit(
                lambda: create_notification_for_new_product.delay(
                    self.company_id, self.id
                )
            )
        if cache.__class__.__module__.startswith("django_redis"):
            try:
                cache.delete_pattern(f"product_flow:company:{self.company_id}:*")
                cache.delete_pattern(f"products:company:{self.company_id}:*")
            except Exception as e:
                pass

    class Meta:
        indexes = [
            models.Index(fields=["company", "category"]),
        ]

    def __str__(self):
        if self.unit == "count":
            return f"{self.name} ({self.unit})"
        return f"{self.name} ({self.quantity} {self.unit})"

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.id})

    def get_qr_code_url(self):
        return f"http://127.0.0.1:8000/api/v1/products/{self.id}"

    def get_total_stock(self):
        result = self.records.aggregate(
            total_pieces=Sum(
                (F("box_quantity") * self.pieces_per_box)
                + F("piece_quantity")
                - F("consumed_quantity"),
                filter=models.Q(record_type="in"),
            )
        )
        total_pieces = result["total_pieces"] or 0
        return {
            "box_quantity": total_pieces // self.pieces_per_box,
            "piece_quantity": total_pieces % self.pieces_per_box,
            "total_pieces": total_pieces,
        }


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image_url = models.URLField(max_length=999)

    def __str__(self):
        return f"Image for {self.product.name} ({self.image_url})"


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
    )
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    record_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new and self.record_type == "out":
                self._consume_stock()
        if cache.__class__.__module__.startswith("django_redis"):
            try:
                cache.delete_pattern(
                    f"product_flow:company:{self.product.company_id}:*"
                )
                cache.delete_pattern(f"products:company:{self.product.company_id}:*")
            except Exception as e:
                pass

    def _consume_stock(self):
        """출고 시 FIFO로 재고 소진 (벌크 업데이트로 최적화)"""
        total_out_pieces = (
            self.box_quantity * self.product.pieces_per_box
        ) + self.piece_quantity
        if total_out_pieces <= 0:
            return

        in_records = (
            self.product.records.filter(record_type="in")
            .exclude(
                consumed_quantity=F("box_quantity") * self.product.pieces_per_box
                + F("piece_quantity")
            )
            .order_by("record_date")
        )

        remaining_out = total_out_pieces
        updates = []
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
            updates.append(in_record)
            remaining_out -= consumed

            if remaining_out <= 0:
                break

        if remaining_out > 0:
            raise ValueError("소진할 재고가 부족합니다.")

        with transaction.atomic():
            for record in updates:
                record.save(update_fields=["consumed_quantity"])

    class Meta:
        indexes = [
            models.Index(fields=["product", "record_date"]),
            models.Index(fields=["record_type"]),
            models.Index(fields=["expiration_date"]),
            models.Index(fields=["record_date", "product"]),
        ]

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.product.name}"


class ProductRecordSnapshot(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="product_snapshots"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="snapshots"
    )
    snapshot_date = models.DateField(default=timezone.now, help_text="스냅샷 날짜")
    box_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], help_text="박스 수량"
    )
    piece_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], help_text="개별 수량"
    )
    total_pieces = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], help_text="총 개수"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if cache.__class__.__module__.startswith("django_redis"):
            try:
                cache.delete_pattern(f"product_flow:company:{self.company_id}:*")
                cache.delete_pattern(f"products:company:{self.company_id}:*")
            except Exception as e:
                pass

    class Meta:
        indexes = [
            models.Index(fields=["company", "snapshot_date"]),
            models.Index(fields=["product", "snapshot_date"]),
            models.Index(fields=["company", "-snapshot_date"]),
            models.Index(fields=["product", "-snapshot_date"]),
        ]
        unique_together = ["company", "product", "snapshot_date"]
        ordering = ["-snapshot_date"]

    def __str__(self):
        return (
            f"{self.company.name} - {self.product.name} Snapshot ({self.snapshot_date})"
        )
