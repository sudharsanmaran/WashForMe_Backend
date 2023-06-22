from rest_framework import serializers

from core.models import Timeslot, BookTimeslot


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = '__all__'
        read_only_fields = ['id', 'start_datetime', 'end_datetime', 'pickup_available_quota',
                            'delivery_available_quota', 'shop']


class GroupedTimeslotSerializer(serializers.Serializer):
    date = serializers.DateField()
    timeslots = TimeslotSerializer(many=True)


class GroupedTimeslotListSerializer(serializers.ListSerializer):
    child = GroupedTimeslotSerializer()


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTimeslot
        fields = '__all__'
        read_only_fields = ['id', 'user']
