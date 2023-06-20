from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.throttling import UserRateThrottle

from core.api.serializers.payment_serializers import PaymentSerializer
from core.constants import PaymentStatus
from core.models import Payment
from core.signals import payment_success_signal


@extend_schema(
    tags=['Payment'],
)
class PaymentListCreateView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()

    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)


@extend_schema(
    tags=['Payment'],
)
class PaymentRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    throttle_classes = [UserRateThrottle]
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    lookup_field = 'id'

    def perform_update(self, serializer):
        payment_before_update = self.get_object()
        serialized_data_before_update = serializer.to_representation(payment_before_update)

        payment = serializer.save()

        serialized_data_after_update = serializer.data

        if (serialized_data_before_update.get('payment_status') != PaymentStatus.SUCCESS.name
                and serialized_data_after_update.get('payment_status') == PaymentStatus.SUCCESS.name):
            payment_success_signal.send(sender=self.__class__, payment_id=payment.id)
