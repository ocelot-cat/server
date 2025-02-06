from rest_framework import serializers
from posts.models import Post, Tag, PostImage


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image")


class PostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True
    )

    class Meta:
        model = Post
        fields = ("id", "tags", "author")

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)

        # 태그 처리
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)

        return post


class PostRetrieveSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "tags",
            "images",
            "likes_count",
            "created_at",
        )

    def get_author(self, obj):
        if obj.author.is_public:
            return obj.author.username
        return None

    def get_likes_count(self, obj):
        return obj.likes.count()


class PostListSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, source="images.all")
    tags = TagSerializer(many=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)

    class Meta:
        model = Post
        fields = ["id", "created_at", "images", "tags", "likes_count"]
        read_only_fields = ["id", "created_at"]
