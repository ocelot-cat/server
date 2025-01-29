from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from posts.models import Post, PostImage, Tag
from posts.serializers import (
    PostCreateSerializer,
    PostRetrieveSerializer,
)
from users.models import UserInterest
from users.serializers import UserSerializer


class PostCreateView(APIView):
    """포스트 생성"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save(author=request.user)

            images = request.FILES.getlist("images")
            for image in images:
                PostImage.objects.create(post=post, image=image)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostsRecommendedView(APIView):
    """추천 포스트 목록"""

    def get(self, request):
        user = request.user
        user_interests = UserInterest.objects.filter(user=user).values("tag")

        recommended_posts = (
            Post.objects.filter(tags__in=user_interests)
            .annotate(
                relevance=Sum(
                    "tags__userinterest__score",
                    filter=F("tags__userinterest__user") == user,
                )
            )
            .order_by("-relevance", "-created_at")[:10]  # 상위 10개 게시물만 추천
        )

        serializer = PostRetrieveSerializer(recommended_posts, many=True)
        return Response(serializer.data)


class TaggedPostsPagination(PageNumberPagination):
    page_size = 10  # 한 페이지에 표시할 게시물 수
    page_size_query_param = "page_size"
    max_page_size = 100


class PostsTaggedView(GenericAPIView):
    """태그별 포스트 목록"""

    serializer_class = PostRetrieveSerializer
    pagination_class = TaggedPostsPagination

    def get_queryset(self):
        tag_name = self.kwargs.get("tag_name")
        tag = get_object_or_404(Tag, name=tag_name)
        return Post.objects.filter(tags=tag).order_by("-created_at")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PostDetailView(APIView):
    """포스트 디테일"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Post, pk=pk)

    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = PostRetrieveSerializer(post)
        return Response(serializer.data)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostLikeView(APIView):
    """포스트에 like,unlike 기능"""

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            action = "취소"
            self.update_user_interest(user, post, -1)
        else:
            post.likes.add(user)
            action = "추가"
            self.update_user_interest(user, post, 1)

        return Response(
            {
                "detail": f"좋아요가 {action}되었습니다.",
                "is_public": post.author.is_public,
            },
            status=status.HTTP_200_OK,
        )

    def update_user_interest(self, user, post, score_change):
        for tag in post.tags.all():
            UserInterest.objects.update_or_create(
                user=user, tag=tag, defaults={"score": F("score") + score_change}
            )


class PostLikesList(APIView):
    """포스트 디테일에 좋아요를 누른 자세한 사용자 목록"""

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        likes = post.likes.all()
        serializer = UserSerializer(likes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
