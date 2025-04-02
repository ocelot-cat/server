from django.db import models
from core.models import CommonModel
from users.models import User


class Notification(CommonModel):
    NOTIFICATION_TYPES = (
        ("product_added", "새 제품 추가"),
        ("member_added", "새 직원 추가"),
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    related_object_id = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.message}"
