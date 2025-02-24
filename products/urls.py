from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProductView.as_view(), name="product"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path(
        "<uuid:uuid>/",
        views.ProductUUIDDetailView.as_view(),
        name="product_uuid_detail",
    ),
    path("<uuid:uuid>/qr/", views.get_product_qr, name="product_qr"),
]
