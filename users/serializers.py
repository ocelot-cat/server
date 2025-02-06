from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from posts.serializers import PostImageSerializer
from .models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.serializers import ModelSerializer, Serializer, CharField


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


class UserCreateSerializer(ModelSerializer):
    """회원 가입"""

    class Meta:
        model = User
        fields = ("username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(ModelSerializer):
    """회원 정보 수정"""

    class Meta:
        model = User
        fields = ("username", "email")


class ChangePasswordSerializer(Serializer):
    old_password = CharField(required=True)
    new_password = CharField(required=True, validators=[validate_password])


class UserSerializer(ModelSerializer):
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ("id", "username")


class UserMeSerializer(ModelSerializer):
    followers = SerializerMethodField()
    followings = SerializerMethodField()
    posts = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_public",
            "followers",
            "followings",
            "posts",
        ]

    def get_followers(self, obj):
        return {
            "count": obj.followers.count(),
            "results": FollowSerializer(obj.followers.all(), many=True).data,
        }

    def get_followings(self, obj):
        return {
            "count": obj.followings.count(),
            "results": FollowSerializer(obj.followings.all(), many=True).data,
        }

    def get_posts(self, obj):
        return {
            "count": obj.posts.count(),
            "results": PostImageSerializer(obj.posts.all(), many=True).data,
        }


# token_obtain_pair
class TokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["id"] = user.id
        return token
