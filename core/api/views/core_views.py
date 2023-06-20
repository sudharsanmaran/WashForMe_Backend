from drf_spectacular.utils import extend_schema
from rest_framework import (
    permissions)

from core.api.serializers.core_serializers import (
    ItemSerializer,
    CategorySerializer)
from core.custom_view_sets import BaseAttrViewSet
from core.models import (
    Item,
    WashCategory)


@extend_schema(
    tags=['Washable Item'],
)
class ItemView(BaseAttrViewSet):
    """Item model views."""
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.all()


@extend_schema(
    tags=['Wash Categories'],
)
class CategoryView(BaseAttrViewSet):
    """WashCategory model views."""
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WashCategory.objects.all()
