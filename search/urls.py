from django.urls import path
from .views import PostSearchView, TagSearchView, UserSearchView

urlpatterns = [
    path("posts/", PostSearchView.as_view(), name="search-posts"),
    path("tags/", TagSearchView.as_view(), name="search-tags"),
    path("users/", UserSearchView.as_view(), name="search-users"),
]
