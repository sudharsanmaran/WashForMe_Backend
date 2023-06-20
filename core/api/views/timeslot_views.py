from datetime import datetime

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.timeslot_serializers import TimeslotSerializer, BookingSerializer
from core.constants import TIMESLOTS_DAYS, BookingType
from core.cron import update_timeslots
from core.models import Timeslot, Shop, BookTimeslot


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
