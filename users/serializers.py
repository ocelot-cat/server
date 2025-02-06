from rest_framework import serializers
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


class UserMeSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    followings_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "is_public",
            "followers_count",
            "followings_count",
            "posts_count",
        ]


# token_obtain_pair
class TokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["id"] = user.id
        return token
