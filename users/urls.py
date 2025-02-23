from django.urls import path
from . import views

urlpatterns = [
    path("", views.UserView.as_view(), name="user"),
    path("", views.UserDetailView.as_view(), name="user_detail"),
    path("company/", views.CompanyView.as_view(), name="company"),
    path("company/<int:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
]
