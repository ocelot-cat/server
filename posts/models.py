from django.db import models

from core.models import CommonModel
from users.models import User


class Tag(CommonModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(CommonModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)

    def __str__(self):
        return f"{self.author.username}'s post"


class PostImage(CommonModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="post_images/")
