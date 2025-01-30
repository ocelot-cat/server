from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from posts.models import Post, Tag
from posts.serializers import PostRetrieveSerializer
from users.models import User
from users.serializers import UserSerializer


class PostSearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if query:
            posts = Post.objects.filter(Q(tags__name__icontains=query)).distinct()
            serializer = PostRetrieveSerializer(posts, many=True)
            return Response(serializer.data)
        return Response([])


class TagSearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if query:
            tags = Tag.objects.filter(name__icontains=query)
            return Response(tags.values_list("name", flat=True))
        return Response([])


class UserSearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if query:
            users = User.objects.filter(username__icontains=query)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        return Response([])
