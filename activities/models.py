from django.db import models
from django.contrib.auth import get_user_model
from core.models import CommonModel

User = get_user_model()


class Activity(CommonModel):
    ACTIVITY_TYPES = (
        ("like", "좋아요"),
        ("follow", "팔로우"),
    )

    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="targeted_activities",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="activities",
        null=True,
        blank=True,
    )
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        if self.activity_type == "like":
            return f"{self.actor.username}님이 게시물에 좋아요를 눌렀습니다."
        elif self.activity_type == "follow":
            return f"{self.actor.username}님이 {self.target_user.username}님을 팔로우했습니다."
        else:
            return "알 수 없는 활동"
