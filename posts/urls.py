from django.urls import path
from . import views

urlpatterns = [
    path("", views.PostCreateView.as_view(), name="post-crete"),
    path("<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
    path(
        "<int:post_id>/likes/",
        views.PostLikesList.as_view(),
        name="post-likes-list",
    ),
]
