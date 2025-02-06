from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_public = models.BooleanField(default=True)
    followings = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["username"], name="username_idx"),
        ]


class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interests")
    tag = models.ForeignKey("posts.Tag", on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "tag")
