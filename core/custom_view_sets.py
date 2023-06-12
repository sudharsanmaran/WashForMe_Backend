from rest_framework import mixins, viewsets, permissions
from rest_framework.throttling import UserRateThrottle


class BaseAttrViewSet(mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    """Base view set for the key attributes."""
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
