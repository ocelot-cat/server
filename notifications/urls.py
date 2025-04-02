from django.urls import path
from . import views

urlpatterns = [
    path("", views.NotificationListAPIView.as_view(), name="notification_list"),
    path(
        "<int:notification_id>/mark-read/",
        views.MarkReadAPIView.as_view(),
        name="mark_read",
    ),
]
