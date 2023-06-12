"""
Views for the user
"""
from rest_framework import (
    permissions,
    generics,
    mixins,
    viewsets,
    authentication,
)

from core.api.serializers.user_serializer import (
    UserSerializer,
    AddressSerializer,
)
from core.models import Address


class UserDetailView(
    generics.RetrieveUpdateAPIView
):
    """Retrieve and update user data."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressDetailsView(mixins.DestroyModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    """Base view set for the key attributes."""
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        queryset = self.queryset

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def perform_create(self, serializer):
        """Create user address."""
        serializer.save(user=self.request.user)
