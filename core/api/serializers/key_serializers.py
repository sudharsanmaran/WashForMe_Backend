"""
Key Serializers.
"""
from rest_framework import (
    serializers,
)

from core.models import (
    Item,
    WashCategory,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'image', 'price', 'count']
        read_only_fields = ['id', 'count']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        fields = ['id', 'name', 'extra_per_item', 'items']
        read_only_fields = ['id']
