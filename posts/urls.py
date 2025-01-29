from django.urls import path
from . import views

urlpatterns = [
    path("", views.PostCreateView.as_view(), name="post-crete"),
    path(
        "recommended/",
        views.PostsRecommendedView.as_view(),
        name="posts-recommended",
    ),
    path("<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
    path("<int:post_id>/like/", views.PostLikeView.as_view(), name="like-post"),
    path(
        "<int:post_id>/likes/",
        views.PostLikesList.as_view(),
        name="post-likes-list",
    ),
]
