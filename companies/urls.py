from django.urls import path
from .views import (
    CompanyMembersListView,
    CompanyPromoteMembersView,
    DepartmentDetailView,
    DepartmentView,
    InvitationCreateView,
    InvitationAcceptView,
    CompanyView,
    CompanyDetailView,
    NotificationListView,
)


urlpatterns = [
    path("", CompanyView.as_view(), name="company"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company_detail"),
    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    path(
        "<int:company_id>/members/",
        CompanyMembersListView.as_view(),
        name="company_members_list",
    ),
    path(
        "<int:company_id>/members/<int:user_id>/promote/",
        CompanyPromoteMembersView.as_view(),
        name="company_members_promote",
    ),
    path(
        "<int:company_id>/departments/",
        DepartmentView.as_view(),
        name="create_department",
    ),
    path(
        "departments/<int:pk>/",
        DepartmentDetailView.as_view(),
        name="department_detail",
    ),
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
