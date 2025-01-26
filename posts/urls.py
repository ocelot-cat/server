from django.urls import path
from . import views

urlpatterns = [
    path(
        "<str:username>",
        views.PostsOwnList.as_view(),
        name="own-posts-list",
    ),
]
