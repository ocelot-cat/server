from rest_framework.serializers import ModelSerializer
from .models import User


# @SubSerializer
class FollowSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")


class UserFollowingsListSerializer(ModelSerializer):
    followings = FollowSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("followings",)

    def get_queryset(self):
        return User.objects.prefetch_related("followings").all()


class UserFollowersListSerializer(ModelSerializer):
    followers = FollowSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("followers",)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")
