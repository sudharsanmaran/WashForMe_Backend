from rest_framework import serializers

from core.models import Timeslot, BookTimeslot, Shop


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


class TimeSlotPickupRequestSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    shop_id = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all(), required=True)
    is_available = serializers.BooleanField(required=False)


class TimeslotDeliveryRequestSerializer(serializers.Serializer):
    is_available = serializers.BooleanField(required=False)

    def get_fields(self):
        fields = super().get_fields()
        user_id = self.context['request'].user.id
        fields['pickup_booking_id'] = serializers.PrimaryKeyRelatedField(
            queryset=BookTimeslot.objects.filter(user_id=user_id), required=True)
        return fields


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTimeslot
        fields = '__all__'
        read_only_fields = ['id', 'user']
