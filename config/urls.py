from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="API 서비스",
        default_version="v1",
        description="API 서비스입니다.",
    ),
    public=True,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0)),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/posts/", include("posts.urls")),
    path("api/v1/activities/", include("activities.urls")),
    path("api/v1/search/", include("search.urls")),
]
