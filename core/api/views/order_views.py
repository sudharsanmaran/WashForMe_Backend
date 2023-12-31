import datetime

from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.order_serializers import (OrderSerializer,
                                                    CartToOrderRequestSerializer,
                                                    OrderDetailsSerializer)
from core.constants import OrderStatus
from core.models import Order, Cart


class OrderFilter(FilterSet):
    updated_at__gte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at__lte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    order_status = filters.ChoiceFilter(
        choices=[(tag.name, tag.value) for tag in OrderStatus],
        field_name='order_status',
        lookup_expr='exact'
    )

    class Meta:
        model = Order
        fields = ['updated_at__gte', 'updated_at__lte', 'order_status']

    def validate_updated_at__gte(self, value):
        if value is not None and value > datetime.now():
            raise filters.ValidationError("updated_at__gte cannot be in the future.")
        return value

    def validate_updated_at__lte(self, value):
        if value is not None and value > datetime.now():
            raise filters.ValidationError("updated_at__lte cannot be in the future.")
        return value


@extend_schema(
    tags=['Orders'],
)
class OrderListCreateAPIView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter


@extend_schema(
    tags=['Orders'],
)
class OrderRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


@extend_schema(
    tags=['Orders'],
    responses=OrderSerializer
)
class CartToOrderAPIView(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartToOrderRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        order_details = []
        for cart_item in cart_items:
            order_detail_data = {
                'product': cart_item.item.id,
                'wash_category': cart_item.wash_category.id,
                'quantity': cart_item.quantity,
            }
            order_detail_serializer = OrderDetailsSerializer(data=order_detail_data)
            order_detail_serializer.is_valid(raise_exception=True)
            order_details.append(order_detail_data)

        order_data = {
            'pickup_booking': serializer.validated_data['pickup_booking'].id,
            'delivery_booking': serializer.validated_data['delivery_booking'].id,
            'order_details': order_details
        }

        order_serializer = OrderSerializer(data=order_data, context={'request': request})
        order_serializer.is_valid(raise_exception=True)
        order_serializer.save()

        cart_items.delete()
        user.cart_total_price = 0
        user.save()

        return Response(order_serializer.data, status=status.HTTP_201_CREATED)
