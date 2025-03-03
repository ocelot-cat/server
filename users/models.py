from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("owner", "사장"),
        ("admin", "관리자"),
        ("employee", "일반직원"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="employee")
