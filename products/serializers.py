from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "quantity",
            "unit",
            "qr_code",
            "received_by",
            "company",
        ]
