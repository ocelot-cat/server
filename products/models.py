from django.db import models
import uuid
from core.models import CommonModel
from users.models import Company, User


from django.db import models
import uuid
from core.models import CommonModel
from users.models import Company, User


class Product(CommonModel):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    piece_quantity = models.IntegerField(default=0)
    box_quantity = models.IntegerField(default=0)
    container_quantity = models.IntegerField(default=0)
    qr_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="products"
    )


class ProductRecord(CommonModel):
    RECORD_TYPE_CHOICES = (
        ("in", "입고"),
        ("out", "출고"),
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_records"
    )
    record_type = models.CharField(max_length=3, choices=RECORD_TYPE_CHOICES)
    piece_quantity = models.IntegerField(default=0)
    box_quantity = models.IntegerField(default=0)
    container_quantity = models.IntegerField(default=0)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    record_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
