from django.urls import path
from . import views

urlpatterns = [
    path("", views.PostCreateView.as_view(), name="post-crete"),  # 포스트 생성
    path(
        "recommended/",
        views.PostsRecommendedView.as_view(),
        name="posts-recommended",
    ),  # 추천 포스트 목록
    path(
        "tag/<str:tag_name>/",
        views.PostsTaggedView.as_view(),
        name="tagged-posts",
    ),  # 태그별 포스트 목록
    path(
        "<int:pk>/", views.PostDetailView.as_view(), name="post-detail"
    ),  # 포스트 디테일
    path(
        "<int:post_id>/like/", views.PostLikeView.as_view(), name="like-post"
    ),  # 포스트 좋아요 및 좋아요 취소
    path(
        "<int:post_id>/likes/",
        views.PostLikesList.as_view(),
        name="post-likes-list",
    ),  # 포스트에 해당하는 좋아요 목록
    path(
        "posts/<int:post_id>/upload-image/",
        views.PostImageUploadView.as_view(),
        name="post-image-upload",  # 사진업로드
    ),
]
