from django.urls import path
from . import views

urlpatterns = [
    path("", views.UserView.as_view(), name="user"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("me/", views.UserMeView.as_view(), name="user_me"),
]
