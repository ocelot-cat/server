from django.urls import reverse
import qrcode
import base64
from io import BytesIO
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from products.models import Product
from .serializers import ProductRecordSerializer, ProductSerializer


class ProductView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            print("Saving product...")
            product = serializer.save()
            print(f"Product saved: {product.id}")
            # 수동으로 시그널 호출
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


class ProductRecordCreateView(APIView):
    def post(self, request, pk, *args, **kwargs):
        # 해당 Product가 존재하는지 확인
        product = get_object_or_404(Product, pk=pk)

        # 요청 데이터에 product와 recorded_by 추가
        data = request.data.copy()
        data["product"] = product.id
        data["recorded_by"] = (
            request.user.id
        )  # 인증된 사용자를 기록자로 설정 (인증 필요)

        serializer = ProductRecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()  # save()에서 expiration_date와 재고가 자동 업데이트됨
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
