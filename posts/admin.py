from django.contrib import admin

from posts.models import Post, PostImage, Tag


@admin.register(Post)
class PostsAdmin(admin.ModelAdmin):
    list_filter = ("author", "likes", "tags")


@admin.register(PostImage)
class PostsImageAdmin(admin.ModelAdmin):
    list_filter = ("post", "image")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_filter = ("name",)
