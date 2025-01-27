from django.urls import path
from .views import UserActivityListView

urlpatterns = [
    path("my", UserActivityListView.as_view(), name="my_activities"),
]
