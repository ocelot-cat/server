import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from users.models import User


def get_expiration_date():
    return timezone.now() + timedelta(days=7)


class Company(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_companies"
    )
    members = models.ManyToManyField(
        User, through="CompanyMembership", related_name="companies"
    )


class CompanyMembership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10,
        choices=(
            ("owner", "사장"),
            ("admin", "관리자"),
            ("employee", "일반직원"),
        ),
        default="employee",
    )

    class Meta:
        unique_together = ("company", "user")


class Invitation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiration_date = models.DateTimeField(default=get_expiration_date)
    is_accepted = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
