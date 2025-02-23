from django.db import models
from django.contrib.auth.models import AbstractUser

from core.models import CommonModel


class User(AbstractUser):
    ROLE_CHOICES = (
        ("owner", "사장"),
        ("admin", "관리자"),
        ("employee", "일반직원"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="employee")


class Company(CommonModel):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_companies"
    )
