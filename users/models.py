from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import CommonModel


class User(AbstractUser):
    pass


class UserProductInterest(CommonModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=["product"]),
        ]
