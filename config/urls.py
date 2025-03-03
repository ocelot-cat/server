from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView


schema_view = get_schema_view(
    openapi.Info(
        title="ocelot-cat API",
        default_version="v1",
        description="ocelot-cat API",
        terms_of_service="https://github.com/ocelot-cat",
        contact=openapi.Contact(email="devscarycat@icloud.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/companies/", include("companies.urls")),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
]
