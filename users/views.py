from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from users.models import User
from users.serializers import (
    UserFollowersListSerializer,
    UserFollowingsListSerializer,
)


class UsersFollowingsList(APIView):
    """내가 팔로우 하는 사람의 리스트 (팔로우 followings)"""

    def get(self, request, username):
        user = get_object_or_404(
            User.objects.prefetch_related("followings"), username=username
        )
        serializer = UserFollowingsListSerializer(user)
        return Response(serializer.data)


class UsersFollowersList(APIView):
    """나를 팔로우 해주는 사람의 리스트 (팔로워 followers)"""

    def get(self, request, username):
        user = get_object_or_404(
            User.objects.prefetch_related("followers"), username=username
        )
        serializer = UserFollowersListSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
