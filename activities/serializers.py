from rest_framework import serializers
from .models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username")

    class Meta:
        model = Activity
        fields = ["id", "activity_type", "actor_username", "created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.activity_type == "like":
            representation["message"] = (
                f"{instance.actor.username}님이 당신의 게시물에 좋아요를 눌렀습니다."
            )
        elif instance.activity_type == "follow":
            representation["message"] = (
                f"{instance.actor.username}님이 당신을 팔로우했습니다."
            )
        return representation
