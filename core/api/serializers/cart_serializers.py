from rest_framework import serializers

from core.api.serializers.core_serializers import ItemSerializer, CategorySerializer
from core.models import Cart


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['id', 'user', 'price']


class CartResponseSerializer(serializers.ModelSerializer):
    item = ItemSerializer()
    wash_category = CategorySerializer()

    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['id', 'user', 'price', 'item', 'wash_category']
