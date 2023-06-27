import logging
from typing import Dict, Any, Optional

import razorpay
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from razorpay.errors import SignatureVerificationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.payment_serializers import (
    RazorpayPaymentRequestSerializer, RazorpayOrderResponseSerializer,
    PaymentSerializer, RazorpayInitiateSerializer, RazorpayPaymentInitiateResponseSerializer,
    RazorpayPartialPaymentSerializer
)
from core.constants import INR_UNIT, PaymentSource, PaymentStatus, OrderStatus
from core.models import Payment, Order, RazorpayPayment

logger = __import__("logging").getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RazorpayPaymentInfoView(APIView):
    throttle_classes = [UserRateThrottle]
    serializer_class = RazorpayInitiateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Razorpay Payment'],
        parameters=[
            OpenApiParameter(name='order_id', required=True, type=str)
        ],
        responses=RazorpayPaymentInitiateResponseSerializer
    )
    def get(self, request):
        order_id = request.query_params.get('order_id')
        serializer = self.serializer_class(data={'order_id': order_id})
        serializer.is_valid(raise_exception=True)
        order_obj = serializer.validated_data['order_id']

        client = RazorpayPaymentInfoView.get_client()

        payment = Payment.objects.filter(order=order_obj,
                                         amount=order_obj.total_price).first()
        if not payment:
            RazorpayPaymentInfoView.delete_payment(order_obj)

            payment_data = RazorpayPaymentInfoView.create_payment(order_obj,
                                                                  request.user.id)

            razorpay_order = RazorpayPaymentInfoView.create_razorpay_order(
                client, order_obj, payment_data.get('id')
            )

            _ = RazorpayPaymentInfoView.create_razorpay_payment(
                payment_data.get('id'), razorpay_order.get('id')
            )
        else:
            payment_serializer = PaymentSerializer(payment)
            payment_data = payment_serializer.data

            razorpay_payment = RazorpayPaymentInfoView.get_razorpay_payment(
                payment
            )

            razorpay_order = RazorpayPaymentInfoView.get_razorpay_order_details(
                client,
                razorpay_payment.razorpay_order_id
            )

        response_data = {
            'payment': payment_data,
            'razorpay': razorpay_order
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def get_client() -> razorpay.Client:
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,
                                     settings.RAZORPAY_KEY_SECRET))

    @staticmethod
    def create_razorpay_order(client: razorpay.Client, order_obj: Order, payment_id: str) -> Dict[str, Any]:
        razorpay_order_data = {
            "amount": int(order_obj.total_price * INR_UNIT),
            "currency": "INR",
            "notes": {
                'wash_for_me_order_id': str(order_obj.id),
                'wash_for_me_payment_id': str(payment_id)
            },
            "partial_payment": False
        }
        razorpay_order = client.order.create(data=razorpay_order_data)
        razorpay_order_serializer = RazorpayOrderResponseSerializer(data=razorpay_order)
        if not razorpay_order_serializer.is_valid():
            logger.warning('razorpay create order api response changed')
        return razorpay_order

    @staticmethod
    def get_razorpay_order_details(client: razorpay.Client, razorpay_order_id: str) -> Optional[Dict[str, Any]]:
        return client.order.fetch(razorpay_order_id)

    @staticmethod
    def create_payment(order_obj: Order, user_id: int) -> Dict[str, Any]:
        payment_data = {
            'user': user_id,
            'order': order_obj.id,
            'amount': order_obj.total_price,
            'payment_source': PaymentSource.RAZORPAY.name,
            'payment_status': PaymentStatus.INITIATED.name,
        }
        payment_serializer = PaymentSerializer(data=payment_data)
        payment_serializer.is_valid(raise_exception=True)
        payment_serializer.save()
        return payment_serializer.data

    @staticmethod
    def delete_payment(order_obj: Order) -> None:
        payment = Payment.objects.filter(order=order_obj)
        if payment:
            payment.delete()
        return

    @staticmethod
    def create_razorpay_payment(payment_id: str,
                                razorpay_order_id: str) -> Dict[str, Any]:
        serializer = RazorpayPartialPaymentSerializer(
            data={'payment': payment_id,
                  'razorpay_order_id': razorpay_order_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data

    @staticmethod
    def get_razorpay_payment(payment: Payment) -> Optional[Dict[str, Any]]:
        return RazorpayPayment.objects.get(payment=payment)


@extend_schema(
    tags=['Razorpay Payment']
)
class RazorpayStatusView(APIView):
    throttle_classes = [UserRateThrottle]
    serializer_class = RazorpayPaymentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        razorpay_order_id = validated_data['razorpay_order_id']
        razorpay_payment_id = validated_data['razorpay_payment_id']
        razorpay_signature = validated_data['razorpay_signature']
        payment = validated_data['payment']

        client = RazorpayPaymentInfoView.get_client()

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except SignatureVerificationError as e:
            return Response({'error': e.args[0]},
                            status=status.HTTP_400_BAD_REQUEST)

        razorpay_payment = RazorpayPayment.objects.get(razorpay_order_id=razorpay_order_id)
        razorpay_payment.razorpay_payment_id = razorpay_payment_id
        razorpay_payment.razorpay_signature = razorpay_signature
        razorpay_payment.save()

        payment.payment_status = PaymentStatus.SUCCESS.name
        payment.save()

        order = payment.order
        order.order_status = OrderStatus.PLACED.name
        order.save()

        return Response('order placed successfully', status=status.HTTP_200_OK)
