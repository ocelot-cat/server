from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from posts.models import Post
from posts.serializers import PostSerializer
from users.serializers import UserSerializer


class PostDetailView(RetrieveAPIView):
    """포스트 디테일"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "pk"


class PostLikesList(APIView):
    """포스트 디테일에 좋아요를 누른 자세한 사용자 목록"""

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        likes = post.likes.all()
        serializer = UserSerializer(likes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
