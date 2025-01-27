from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from posts.models import Post
from users.models import User
from .models import Activity


@receiver(m2m_changed, sender=Post.likes.through)
def create_like_activity(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_pk in pk_set:
            Activity.objects.create(
                actor=User.objects.get(pk=user_pk),
                recipient=instance.author,
                post=instance,
                activity_type="like",
            )


@receiver(m2m_changed, sender=User.followings.through)
def create_follow_activity(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_pk in pk_set:
            Activity.objects.create(
                actor=instance,
                recipient=User.objects.get(pk=user_pk),
                activity_type="follow",
            )
