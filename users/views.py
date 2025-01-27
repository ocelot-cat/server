from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from users.models import User
from posts.models import Post
from users.serializers import (
    UserFollowersListSerializer,
    UserFollowingsListSerializer,
)
from posts.serializers import PostSerializer


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


class PostsOwnList(APIView):
    """사용자가 소유한 포스트 리스트"""

    # 추후 파지네이션 포스트가 늘어날걸 대비해서 파지네이션 진행해야함

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user).prefetch_related(
            "tags", "likes", "images"
        )
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
