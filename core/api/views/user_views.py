"""
Views for the user
"""
from rest_framework import (
    permissions,
    generics,
    mixins,
    viewsets,
    authentication, status,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.user_serializer import (
    UserSerializer,
    AddressSerializer,
)
from core.api.views.login_views import SendOTPView, generate_otp
from core.models import Address


class UserDetailView(
    generics.RetrieveUpdateAPIView
):
    """Retrieve and update user data."""
    throttle_classes = [UserRateThrottle]
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        if 'phone' in request.data:
            response = SendOTPView.send_otp(request.data.get('phone'), generate_otp())
            if response['send']:
                return super().update(request, *args, **kwargs)
            return Response({'message': response['message']}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)


class UpdatePhone(APIView):
    throttle_classes = [UserRateThrottle]


class AddressDetailsView(mixins.DestroyModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    """Base view set for the key attributes."""
    throttle_classes = [UserRateThrottle]
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
