from django.urls import path
from . import views

urlpatterns = [
    path(
        "<str:username>/followings",
        views.UsersFollowingsList.as_view(),
        name="followings-list",
    ),
    path(
        "<str:username>/followers",
        views.UsersFollowersList.as_view(),
        name="followers-list",
    ),
    path(
        "<str:username>/posts",
        views.PostsOwnList.as_view(),
        name="own-posts-list",
    ),
]
