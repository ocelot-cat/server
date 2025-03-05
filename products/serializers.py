from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "piece_quantity",
            "box_quantity",
            "container_quantity",
            "updated_at",
        ]
