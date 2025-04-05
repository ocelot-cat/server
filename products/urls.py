from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProductView.as_view(), name="product"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("<int:pk>/qr/", views.get_product_qr, name="product_qr"),
    path(
        "<int:pk>/records/",
        views.ProductRecordCreateView.as_view(),
        name="product_record_create",
    ),
]
