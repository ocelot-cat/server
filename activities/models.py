from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Activity(models.Model):
    ACTIVITY_TYPES = (
        ("like", "좋아요"),
        ("follow", "팔로우"),
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_activities"
    )
    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="performed_activities"
    )
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
        ]

    def __str__(self):
        if self.activity_type == "like":
            return f"{self.actor.username}님이 게시물에 좋아요를 눌렀습니다."
        elif self.activity_type == "follow":
            return f"{self.actor.username}님이 {self.recipient.username}님을 팔로우했습니다."
        else:
            return "알 수 없는 활동"
