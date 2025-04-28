import uuid
from celery.exceptions import OperationalError
from redis.exceptions import ConnectionError
from django.db import models
from django.utils import timezone
from datetime import timedelta
from config.celery import app as celery_app
from core.models import CommonModel
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

    def __str__(self):
        return self.name


class CompanyMembership(CommonModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="company_membership"
    )
    role = models.CharField(
        max_length=10,
        choices=(
            ("owner", "사장"),
            ("admin", "관리자"),
            ("employee", "일반직원"),
        ),
        default="employee",
    )
    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from companies.tasks import create_notification_for_new_member

            conn = celery_app.connection()
            try:
                conn.connect()
                create_notification_for_new_member.delay(self.company_id, self.id)
            except (OperationalError, ConnectionError):
                create_notification_for_new_member(self.company_id, self.id)

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.get_role_display()})"


# 부서 모델
class Department(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="departments"
    )

    def __str__(self):
        return f"{self.name} ({self.company.name})"


def get_expiration_date():
    return timezone.now() + timedelta(days=7)


class Invitation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiration_date = models.DateTimeField(default=get_expiration_date)
    is_accepted = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expiration_date"]),
        ]

    def __str__(self):
        return f"Invitation to {self.company.name} for {self.email}"


# 알림모델


class Notification(models.Model):
    # 알림 카테고리 선택지
    CATEGORY_CHOICES = (
        ("member_created", "멤버 생성"),
        ("product_created", "제품 생성"),
    )

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    object_id = models.PositiveIntegerField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["category"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"
