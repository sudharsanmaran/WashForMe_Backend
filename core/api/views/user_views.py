from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import (
    generics,
    status,
    permissions,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from drf_spectacular.utils import extend_schema


from core.api.serializers.user_serializer import (
    UserSerializer,
    AddressSerializer,
)

from core.api.views.login_views import SendOTPView, generate_otp
from core.custom_view_sets import BaseAttrViewSet
from core.models import Address


@extend_schema(
    tags=['User Details'],
)
class UserDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update user data."""
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @staticmethod
    def update_user_total_price(user: settings.AUTH_USER_MODEL, price: float, increment: bool) -> None:
        if increment:
            user.total_price += price
        else:
            user.total_price -= price
        user.save()
        return

    def update(self, request, *args, **kwargs):
        if 'phone' in request.data:
            response = SendOTPView.send_otp(request.data.get('phone'), generate_otp())
            if not response['send']:
                return Response({'message': response['message']}, status=status.HTTP_400_BAD_REQUEST)

            super().update(request, *args, **kwargs)
            user = self.get_object()
            user.is_phone_verified = False
            user.save()
            return
        return super().update(request, *args, **kwargs)


@extend_schema(
    tags=['Address'],
)
class AddressDetailsView(BaseAttrViewSet):
    """AddressDetails model views."""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Address.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

