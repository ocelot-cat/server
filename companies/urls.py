from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryCompositionView,
    CompanyMemberDetailView,
    CompanyViewSet,
    CompanyMembersListView,
    CompanyPromoteMembersView,
    DepartmentViewSet,
    InvitationCreateView,
    InvitationAcceptView,
    NotificationListView,
    NotificationMarkReadView,
    ProductListView,
    WeeklyProductFlowView,
)

router = DefaultRouter()
router.register(r"", CompanyViewSet, basename="company")
router.register(r"departments", DepartmentViewSet, basename="department")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:company_id>/members/",
        CompanyMembersListView.as_view(),
        name="company_members_list",
    ),
    path(
        "<int:company_id>/members/<int:user_id>/",
        CompanyMemberDetailView.as_view(),
        name="company_member_detail",
    ),
    path(
        "<int:company_id>/members/<int:user_id>/role/",
        CompanyPromoteMembersView.as_view(),
        name="company_members_role",
    ),
    path(
        "<int:company_id>/invitations/",
        InvitationCreateView.as_view(),
        name="create_invitation",
    ),
    path(
        "invitations/accept/",
        InvitationAcceptView.as_view(),
        name="accept_invitation",
    ),
    path(
        "<int:company_id>/notifications/",
        NotificationListView.as_view(),
        name="notification_list",
    ),
    path(
        "notifications/<int:id>/mark-read/",
        NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    path("<int:company_id>/products/", ProductListView.as_view(), name="product_list"),
    path(
        "<int:company_id>/product-flow/",
        WeeklyProductFlowView.as_view(),
        name="weekly_product_flow",
    ),
    path(
        "<int:company_id>/category-composition/",
        CategoryCompositionView.as_view(),
        name="category_composition",
    ),
]
