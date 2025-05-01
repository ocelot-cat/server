import qrcode
import base64
from io import BytesIO
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.fields import parse_datetime
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from products.models import Product, ProductRecord
from .serializers import (
    ProductRecordSerializer,
    ProductSerializer,
)


class ProductView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            from django.db.models.signals import post_save

            post_save.send(sender=Product, instance=product, created=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductRecordCreateView(APIView):
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        data = request.data.copy()
        data["product"] = product.id
        data["recorded_by"] = request.user.id

        serializer = ProductRecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return image_base64


@api_view(["GET"])
def get_product_qr(request, pk):
    product = get_object_or_404(Product, pk=pk)
    qr_image = generate_qr_code(str(product.pk))
    return Response({"qr_code": qr_image})


class ProductRecordPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductRecordListView(ListCreateAPIView):
    serializer_class = ProductRecordSerializer
    pagination_class = ProductRecordPagination

    def get_queryset(self):
        product_id = self.kwargs["pk"]
        queryset = ProductRecord.objects.filter(product_id=product_id).order_by(
            "-record_date"
        )
        record_type = self.request.query_params.get("record_type")
        if record_type in ["in", "out"]:
            queryset = queryset.filter(record_type=record_type)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date and end_date:
            try:
                start_date = parse_datetime(start_date)
                end_date = parse_datetime(end_date)
                if not start_date or not end_date:
                    raise ValidationError(
                        "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                    )
                if start_date > end_date:
                    raise ValidationError("시작일은 종료일보다 늦을 수 없습니다.")
            except ValueError:
                raise ValidationError(
                    "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                )
        elif start_date:
            try:
                start_date = parse_datetime(start_date)
                if not start_date:
                    raise ValidationError(
                        "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                    )
            except ValueError:
                raise ValidationError(
                    "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                )
        elif end_date:
            try:
                end_date = parse_datetime(end_date)
                if not end_date:
                    raise ValidationError(
                        "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                    )
            except ValueError:
                raise ValidationError(
                    "맞지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하십시오."
                )

        if start_date:
            queryset = queryset.filter(record_date__gte=start_date)
        if end_date:
            end_date = end_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            queryset = queryset.filter(record_date__lte=end_date)

        return queryset.select_related("product", "recorded_by")

    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)

        data = request.data.copy()
        data["product"] = product.id
        data["recorded_by"] = request.user.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
