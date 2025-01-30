from rest_framework import serializers
from .models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    actor_username = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ["id", "activity_type", "actor_username", "created_at"]

    def get_actor_username(self, obj):
        return obj.actor.username if obj.actor.is_public else "익명의 사용자"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        actor_name = self.get_actor_username(instance)
        if instance.activity_type == "like":
            representation["message"] = (
                f"{actor_name}님이 당신의 게시물에 좋아요를 눌렀습니다."
            )
        elif instance.activity_type == "follow":
            representation["message"] = f"{actor_name}님이 당신을 팔로우했습니다."
        return representation
