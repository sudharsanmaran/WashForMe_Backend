"""
Views for key classes.
"""
from rest_framework import (
    mixins,
    viewsets,
    authentication,
    permissions,
)

from core.models import (
    Item,
    Category,
)
from core.api.serializers.key_serializers import (
    ItemSerializer,
    CategorySerializer,
)


class BaseAttrViewSet(mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    """Base view set for the key attributes."""
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ItemView(BaseAttrViewSet):
    """Item model views."""
    serializer_class = ItemSerializer
    queryset = Item.objects.all()


class CategoryView(BaseAttrViewSet):
    """Category model views."""
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
