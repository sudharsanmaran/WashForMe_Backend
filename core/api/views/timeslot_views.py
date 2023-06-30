import itertools
from datetime import datetime, timedelta

from django.db.models import Q
from django_filters import filters
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.timeslot_serializers import (
    BookingSerializer, GroupedTimeslotListSerializer,
    TimeSlotPickupRequestSerializer, TimeslotDeliveryRequestSerializer)
from core.constants import TIMESLOTS_DAYS, BookingType
from core.cron import update_timeslots
from core.models import Timeslot, BookTimeslot


@extend_schema(
    tags=['Timeslots'],
)
class UpdateTimeslots(APIView):
    def put(self, request, *args, **kwargs):
        update_timeslots()
        return Response(data=f'timeslots for all shop are updated for {TIMESLOTS_DAYS} days', status=status.HTTP_200_OK)


class TimeslotListAPIView(APIView):
    """Timeslots base class"""
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupedTimeslotListSerializer

    def get_queryset(self, **kwargs):
        raise NotImplementedError()

    def get_grouped_timeslots(self, timeslots):
        grouped_timeslots = {}
        for date, group in itertools.groupby(timeslots, key=lambda t: t.start_datetime.date()):
            grouped_timeslots[date] = list(group)
        return grouped_timeslots

    def get_available_timeslots(self, start_datetime, end_datetime, shop_id):
        booked_timeslots = BookTimeslot.objects.filter(
            Q(time_slot__start_datetime__range=[start_datetime, end_datetime]) |
            Q(time_slot__end_datetime__range=[start_datetime, end_datetime]),
            time_slot__shop_id=shop_id,
            user_id=self.request.user.id
        ).values_list('time_slot__id', flat=True)

        available_timeslots = Timeslot.objects.filter(
            start_datetime__gte=start_datetime,
            end_datetime__lte=end_datetime,
            shop_id=shop_id
        ).exclude(id__in=booked_timeslots)

        return available_timeslots

    def get(self, request, *args, **kwargs):

        timeslots = self.get_queryset()

        grouped_timeslots = self.get_grouped_timeslots(timeslots)

        grouped_timeslot_list = [{'date': date, 'timeslots': timeslots} for date, timeslots in
                                 grouped_timeslots.items()]

        serializer = GroupedTimeslotListSerializer(grouped_timeslot_list)

        return Response(serializer.data)


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='shop_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ]
)
class PickupTimeslotListAPIView(TimeslotListAPIView):
    """pickup timeslots"""
    serializer_class = GroupedTimeslotListSerializer

    def get_queryset(self, **kwargs):
        serializer = TimeSlotPickupRequestSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        shop = serializer.validated_data['shop_id']
        is_available = bool(serializer.validated_data['is_available'] == 'true')

        start_datetime = datetime.utcnow()
        end_datetime = datetime.utcnow() + timedelta(days=TIMESLOTS_DAYS)

        queryset = self.get_available_timeslots(start_datetime, end_datetime, shop.id)

        if is_available:
            queryset = queryset.filter(pickup_available_quota__gte=1)

        return queryset


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='pickup_booking_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ],
    responses=GroupedTimeslotListSerializer
)
class DeliveryTimeslotListAPIView(TimeslotListAPIView):
    """delivery timeslots"""
    serializer_class = GroupedTimeslotListSerializer

    def get_queryset(self, **kwargs):
        serializer = TimeslotDeliveryRequestSerializer(data=self.request.query_params,
                                                       context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        pickup_booking = serializer.validated_data['pickup_booking_id']
        is_available = bool(serializer.validated_data['is_available'] == 'true')

        time_slot = pickup_booking.time_slot
        shop = time_slot.shop
        pickup_datetime = time_slot.start_datetime

        start_datetime = pickup_datetime + shop.wash_duration
        end_datetime = pickup_datetime + shop.wash_duration + timedelta(days=TIMESLOTS_DAYS)

        queryset = self.get_available_timeslots(start_datetime, end_datetime, shop.id)

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

        if booking_type == BookingType.PICKUP.name:
            if timeslot.pickup_available_quota <= 0:
                return Response({'error': 'No available pickup quota for this timeslot'},
                                status=status.HTTP_400_BAD_REQUEST)
            timeslot.pickup_available_quota -= 1

        elif booking_type == BookingType.DELIVERY.name:
            if timeslot.delivery_available_quota <= 0:
                return Response({'error': 'No available delivery quota for this timeslot'},
                                status=status.HTTP_400_BAD_REQUEST)
            timeslot.delivery_available_quota -= 1

        serializer.save(user=user)
        timeslot.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookTimeslotFilter(FilterSet):
    updated_at__gte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at__lte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    booking_type = filters.ChoiceFilter(
        choices=[(tag.name, tag.value) for tag in BookingType],
        field_name='booking_type',
        lookup_expr='exact'
    )

    class Meta:
        model = BookTimeslot
        fields = ['updated_at__gte', 'updated_at__lte', 'booking_type']

    def validate_updated_at__gte(self, value):
        if value is not None and value > datetime.now():
            raise filters.ValidationError("updated_at__gte cannot be in the future.")
        return value

    def validate_updated_at__lte(self, value):
        if value is not None and value > datetime.now():
            raise filters.ValidationError("updated_at__lte cannot be in the future.")
        return value


@extend_schema(
    tags=['BookTimeslot'],
)
class BookingListView(ListAPIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = BookTimeslot.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookTimeslotFilter
