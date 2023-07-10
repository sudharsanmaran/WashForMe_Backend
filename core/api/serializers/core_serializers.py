
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
        fields = '__all__'
        read_only_fields = ['id', 'count']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        fields = '__all__'
        read_only_fields = ['id']










