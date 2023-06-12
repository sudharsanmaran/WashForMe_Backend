"""
Key Serializers.
"""
from rest_framework import (
    serializers,
)

from core.models import (
    Item,
    WashCategory, UserItem,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'image', 'price', 'count']
        read_only_fields = ['id', 'count']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        fields = ['id', 'name', 'extra_per_item']
        read_only_fields = ['id']


class UserItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserItem
        fields = ['id', 'item', 'quantity', 'wash_category', 'price']
        read_only_fields = ['id', 'user', 'price']
