from django.urls import path
from .views import (
    InvitationCreateView,
    InvitationAcceptView,
    CompanyView,
    CompanyDetailView,
)


urlpatterns = [
    path("", CompanyView.as_view(), name="company"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company_detail"),
    path(
        "<int:company_id>/invite/",
        InvitationCreateView.as_view(),
        name="create_invitation",
    ),
    path(
        "<str:token>/accept/",
        InvitationAcceptView.as_view(),
        name="accept_invitation",
    ),
]
