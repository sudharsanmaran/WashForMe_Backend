from rest_framework import serializers

from core.models import Timeslot, BookTimeslot


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = '__all__'
        read_only_fields = ['id', 'shop', 'start_datetime', 'end_datetime']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTimeslot
        fields = '__all__'
        read_only_fields = ['id', 'user']
