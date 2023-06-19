import uuid
from datetime import datetime

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import (
    permissions,
    generics,
    status, )
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.key_serializers import (
    ItemSerializer,
    CategorySerializer, CartSerializer, ShopSerializer, TimeslotSerializer, BookingSerializer,
    PaymentSerializer, OrderSerializer, )
from core.custom_view_sets import BaseAttrViewSet
from core.models import (
    Item,
    WashCategory, Cart, Shop, Timeslot, BookTimeslot, Payment, Order, )
from .user_views import UserDetailView
from ...constants import TIMESLOTS_DAYS, BookingType, PaymentStatus
from ...cron import update_timeslots
from ...signals import create_shop_timeslots_signal, delete_shop_timeslots_signal, payment_success_signal


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


@extend_schema(tags=['Cart'])
class CartListCreateView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @staticmethod
    def item_price(item_id: uuid.UUID) -> float:
        item = Item.objects.get(pk=item_id)
        return item.price

    @staticmethod
    def wash_category_price(wash_category_id: uuid.UUID) -> float:
        wash_category = WashCategory.objects.get(pk=wash_category_id)
        return wash_category.extra_per_item

    @staticmethod
    def calculate_price(item_id: uuid.UUID, wash_category_id: uuid.UUID, quantity: int) -> float:
        return (CartListCreateView.item_price(item_id) +
                CartListCreateView.wash_category_price(wash_category_id)) * quantity

    def post(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        quantity = int(request.data.get('quantity', 1))

        calculated_price = CartListCreateView.calculate_price(item_id, wash_category_id, quantity)
        UserDetailView.update_user_total_price(user, calculated_price, increment=True)

        existing_user_item = Cart.objects.filter(user=user, item_id=item_id,
                                                 wash_category_id=wash_category_id).first()
        if existing_user_item:
            existing_user_item.quantity += quantity
            existing_user_item.price += calculated_price
            existing_user_item.save()
            serializer = self.get_serializer(existing_user_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, price=calculated_price)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=['Cart'],
)
class CartListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        quantity = int(request.data.get('quantity', 1))
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if not wash_category_id:
            wash_category_id = instance.wash_category_id
        if not item_id:
            item_id = instance.item_id

        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        calculated_price = CartListCreateView.calculate_price(item_id, wash_category_id, quantity)
        UserDetailView.update_user_total_price(user, calculated_price, increment=True)

        instance.quantity = quantity
        instance.price = calculated_price
        instance.item_id = item_id
        instance.wash_category_id = wash_category_id
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Shop Details'],
)
class ShopDetailsView(BaseAttrViewSet):
    """AddressDetails model views."""
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Shop.objects.all()

    def perform_create(self, serializer):
        shop = serializer.save(user=self.request.user)
        create_shop_timeslots_signal.send(sender=self.__class__, shop=shop)

    def perform_update(self, serializer):
        shop_before_update = self.get_object()
        serialized_data_before_update = serializer.to_representation(shop_before_update)

        shop = serializer.save()

        serialized_data_after_update = serializer.data

        fields_to_check = ['active', 'opening_time', 'closing_time', 'wash_duration', 'time_slot_duration',
                           'max_user_limit_per_time_slot']

        if any(serialized_data_before_update[field] != serialized_data_after_update[field] for field in
               fields_to_check):
            delete_shop_timeslots_signal.send(sender=self.__class__, shop=shop)
            if shop.active:
                create_shop_timeslots_signal.send(sender=self.__class__, shop=shop)

    def perform_destroy(self, instance):
        delete_shop_timeslots_signal.send(sender=self.__class__, shop=instance)
        instance.delete()


# @extend_schema(
#     tags=['Shop Review'],
# )
# class ShopReviewView(BaseAttrViewSet):
#     """AddressDetails model views."""
#     serializer_class = ShopReviewSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     queryset = Review.objects.all()
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

@extend_schema(
    tags=['Timeslots'],
)
class UpdateTimeslots(APIView):
    def put(self, request, *args, **kwargs):
        update_timeslots()
        return Response(data=f'timeslots for all shop are updated for {TIMESLOTS_DAYS} days', status=status.HTTP_200_OK)


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='start_date', type=str),
        OpenApiParameter(name='end_date', type=str),
        OpenApiParameter(name='shop_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ]
)
class PickupTimeslotListAPIView(generics.ListAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TimeslotSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        shop_id = self.request.query_params.get('shop_id')
        is_available = bool(self.request.query_params.get('is_available') == 'true')
        try:
            if start_date:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('date must be in date format like \'yyyy-mm-dd\'')

        queryset = Timeslot.objects.all()

        if not start_date:
            start_datetime = datetime.utcnow()
        queryset = queryset.filter(start_datetime__gte=start_datetime)

        if end_date and end_datetime:
            queryset = queryset.filter(end_datetime__lte=end_datetime)
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if is_available:
            queryset = queryset.filter(pickup_available_quota__gte=1)

        return queryset


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='pickup_datetime', required=True, type=str),
        OpenApiParameter(name='shop_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ]
)
class DeliveryTimeslotListAPIView(generics.ListAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TimeslotSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        pickup_datetime = self.request.query_params.get('pickup_datetime')
        shop_id = self.request.query_params.get('shop_id')
        shop = Shop.objects.filter(pk=shop_id).first()
        is_available = bool(self.request.query_params.get('is_available') == 'true')
        try:
            if pickup_datetime:
                pickup_datetime = datetime.strptime(pickup_datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValidationError('datetime must be in format like this example, \'YYYY-mm-dd HH:MM:SS\'')

        queryset = Timeslot.objects.all()

        if not pickup_datetime:
            raise ValidationError('datetime must be in format like this example, \'YYYY-mm-dd HH:MM:SS\'')
        if not shop:
            raise ValidationError('wrong shop_id')

        queryset = queryset.filter(start_datetime__gte=pickup_datetime + shop.wash_duration).filter(shop_id=shop_id)

        if is_available:
            queryset = queryset.filter(delivery_available_quota__gte=1)

        return queryset


@extend_schema(
    tags=['BookTimeslot'],
)
class BookingAPIView(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        timeslot = validated_data['time_slot']
        booking_type = validated_data['booking_type']
        user = request.user

        if BookTimeslot.objects.filter(time_slot=timeslot, user=user).exists():
            return Response({'error': 'User has already booked this timeslot'}, status=status.HTTP_400_BAD_REQUEST)

        if booking_type == BookingType.PICK_UP.value:
            if timeslot.pickup_available_quota <= 0:
                return Response({'error': 'No available pickup quota for this timeslot'},
                                status=status.HTTP_400_BAD_REQUEST)
            timeslot.pickup_available_quota -= 1

        elif booking_type == BookingType.DELIVERY.value:
            if timeslot.delivery_available_quota <= 0:
                return Response({'error': 'No available delivery quota for this timeslot'},
                                status=status.HTTP_400_BAD_REQUEST)
            timeslot.delivery_available_quota -= 1

        serializer.save(user=user)
        timeslot.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['BookTimeslot'],
)
class BookingListView(ListAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = BookTimeslot.objects.all()


@extend_schema(
    tags=['Payment'],
)
class PaymentListCreateView(generics.ListCreateAPIView):
    """AddressDetails model views."""
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
    """AddressDetails model views."""
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


@extend_schema(
    tags=['Orders'],
)
class OrderListCreateAPIView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


@extend_schema(
    tags=['Orders'],
)
class OrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
