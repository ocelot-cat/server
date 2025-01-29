from django.urls import path
from . import views

urlpatterns = [
    path(
        "", views.UserView.as_view(), name="user_operations"
    ),  # 회원정보 수정,삭제,탈퇴
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),  # 비밀번호 변경
    path(
        "<str:username>/followings",
        views.UsersFollowingsList.as_view(),
        name="followings-list",
    ),  # 팔로잉 리스트
    path(
        "<str:username>/followers",
        views.UsersFollowersList.as_view(),
        name="followers-list",
    ),  # 팔로워 리스트
    path(
        "<str:username>/follow/",
        views.UserFollowView.as_view(),
        name="follow-user",
    ),  # 팔로우,언팔로우
    path(
        "<str:username>/posts",
        views.PostsOwnList.as_view(),
        name="own-posts-list",
    ),  # 사용자가 작성한 포스트 리스트
]
