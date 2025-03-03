from django.urls import path
from . import views

urlpatterns = [
    path("", views.UserView.as_view(), name="user"),
    path("", views.UserDetailView.as_view(), name="user_detail"),
]
