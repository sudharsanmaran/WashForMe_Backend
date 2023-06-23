import itertools
from datetime import datetime

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


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='start_date', type=str),
        OpenApiParameter(name='end_date', type=str),
        OpenApiParameter(name='shop_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ]
)
class PickupTimeslotListAPIView(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupedTimeslotListSerializer

    def get(self, request, *args, **kwargs):
        serializer = TimeSlotPickupRequestSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        timeslots = self.get_queryset()

        grouped_timeslots = {}
        for date, group in itertools.groupby(timeslots, key=lambda t: t.start_datetime.date()):
            grouped_timeslots[date] = list(group)

        grouped_timeslot_list = [{'date': date, 'timeslots': timeslots} for date, timeslots in
                                 grouped_timeslots.items()]

        serializer = GroupedTimeslotListSerializer(grouped_timeslot_list)

        return Response(serializer.data)

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        shop_id = self.request.query_params.get('shop_id')
        is_available = bool(self.request.query_params.get('is_available') == 'true')

        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

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
        OpenApiParameter(name='pickup_booking_id', required=True, type=str),
        OpenApiParameter(name='is_available', type=bool),
    ]
)
class DeliveryTimeslotListAPIView(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupedTimeslotListSerializer

    def get(self, request, *args, **kwargs):
        serializer = TimeslotDeliveryRequestSerializer(data=self.request.query_params, context={'request': request})
        serializer.is_valid(raise_exception=True)

        timeslots = self.get_queryset(serializer.validated_data['pickup_booking_id'])

        grouped_timeslots = {}
        for date, group in itertools.groupby(timeslots, key=lambda t: t.start_datetime.date()):
            grouped_timeslots[date] = list(group)

        grouped_timeslot_list = [{'date': date, 'timeslots': timeslots} for date, timeslots in
                                 grouped_timeslots.items()]

        serializer = GroupedTimeslotListSerializer(grouped_timeslot_list)

        return Response(serializer.data)

    def get_queryset(self, pickup_booking: BookTimeslot):
        time_slot = pickup_booking.time_slot
        shop = time_slot.shop
        pickup_datetime = time_slot.start_datetime
        is_available = bool(self.request.query_params.get('is_available') == 'true')

        queryset = Timeslot.objects.all()

        queryset = queryset.filter(
            start_datetime__gte=pickup_datetime + shop.wash_duration
        ).filter(shop_id=shop.id)

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

        if booking_type == BookingType.PICKUP.value:
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
