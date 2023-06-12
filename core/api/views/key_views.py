"""
Views for key classes.
"""
from rest_framework import (
    mixins,
    viewsets,
    authentication,
    permissions,
)
from rest_framework.throttling import UserRateThrottle

from core.models import (
    Item,
    WashCategory,
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
    throttle_classes = [UserRateThrottle]
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ItemView(BaseAttrViewSet):
    """Item model views."""
    throttle_classes = [UserRateThrottle]
    serializer_class = ItemSerializer
    queryset = Item.objects.all()


class CategoryView(BaseAttrViewSet):
    """WashCategory model views."""
    throttle_classes = [UserRateThrottle]
    serializer_class = CategorySerializer
    queryset = WashCategory.objects.all()
