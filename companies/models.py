from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
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
    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:  # 모든 새로운 멤버 추가 시 트리거
            from companies.tasks import create_notification_for_new_member

            create_notification_for_new_member.delay(self.company_id, self.id)

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]
        unique_together = ("company", "user")

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
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    target_url = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"
