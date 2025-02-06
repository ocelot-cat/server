from django.core.cache import cache
from django.db.models import Count, Prefetch
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from posts.serializers import PostListSerializer, PostRetrieveSerializer
from users.models import User
from posts.models import Post, PostImage, Tag
from users.serializers import (
    ChangePasswordSerializer,
    FollowSerializer,
    UserCreateSerializer,
    UserFollowersListSerializer,
    UserFollowingsListSerializer,
    UserMeSerializer,
    UserUpdateSerializer,
)


class UserView(APIView):
    """회원 가입, 정보 수정, 탈퇴"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        - 계정 임시 비활성화 상태로만 변경하려면 -
        user.is_active = False
        user.save()
        """
        user = request.user
        user.delete()
        return Response(
            {"detail": "User successfully deactivated."},
            status=status.HTTP_204_NO_CONTENT,
        )


class UserMeView(APIView):
    """내 정보 조회"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_object_or_404(
            User.objects.annotate(
                followers_count=Count("followers"),
                followings_count=Count("followings"),
                posts_count=Count("posts"),
            ),
            id=request.user.id,
        )
        serializer = UserMeSerializer(user)
        return Response(serializer.data)


class PostPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PostsOwnList(APIView):
    """사용자 포스트 목록"""

    pagination_class = PostPagination

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        queryset = (
            Post.objects.filter(author=user)
            .select_related("author")
            .prefetch_related(
                Prefetch("images", queryset=PostImage.objects.only("id", "image")),
                Prefetch("tags", queryset=Tag.objects.only("id", "name")),
            )
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class FollowPagination(PageNumberPagination):
    """팔로우 리스트 페이지네이션"""

    page_size = 10
    page_size_query_param = "page_size"


class UsersFollowingsList(APIView):
    """내가 팔로우 하는 사람의 리스트 (팔로우 followings)"""

    pagination_class = FollowPagination

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        followings = user.followings.all().only("id", "username")
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(followings, request)
        serializer = FollowSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UsersFollowersList(APIView):
    """나를 팔로우 해주는 사람의 리스트 (팔로워 followers)"""

    def get(self, request, username):
        cache_key = f"user_followers_{username}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        user = get_object_or_404(
            User.objects.prefetch_related("followers"), username=username
        )
        serializer = UserFollowersListSerializer(user)
        cache.set(cache_key, serializer.data, timeout=60 * 15)
        return Response(serializer.data)


class UserFollowView(APIView):
    """팔로우, 언팔로우"""

    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        user = request.user

        if user == user_to_follow:
            return Response(
                {"detail": "자기 자신을 팔로우할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_to_follow in user.followings.all():
            user.followings.remove(user_to_follow)
            action = "언팔로우"
        else:
            user.followings.add(user_to_follow)
            action = "팔로우"

        return Response(
            {"detail": f"{action}되었습니다.", "is_public": user_to_follow.is_public},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """ "비밀번호 변경"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get("old_password")):
                user.set_password(serializer.data.get("new_password"))
                user.save()
                return Response(
                    {"message": "비밀번호가 성공적으로 변경되었습니다."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "현재 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
