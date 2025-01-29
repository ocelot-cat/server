from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from posts.serializers import PostRetrieveSerializer
from users.models import User
from posts.models import Post
from users.serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserFollowersListSerializer,
    UserFollowingsListSerializer,
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


class UserFollowView(APIView):
    """팔로우, 언팔로우"""

    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        user = request.user

        if user == user_to_follow:
            return Response(
                {"detail": "자기 자신은 최고의 친구입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_to_follow in user.followings.all():
            user.followings.remove(user_to_follow)
            return Response(
                {"detail": "언팔로우되었습니다."}, status=status.HTTP_200_OK
            )
        else:
            user.followings.add(user_to_follow)
            return Response(
                {"detail": "팔로우되었습니다."}, status=status.HTTP_201_CREATED
            )


class PostsOwnList(APIView):
    """사용자가 소유한 포스트 리스트"""

    # 추후 파지네이션 포스트가 늘어날걸 대비해서 파지네이션 진행해야함

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user).prefetch_related(
            "tags", "likes", "images"
        )
        serializer = PostRetrieveSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
