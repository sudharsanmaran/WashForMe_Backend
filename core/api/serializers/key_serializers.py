"""
Key Serializers.
"""
from rest_framework import (
    serializers,
)

from core.constants import BookingType
from core.models import (
    Item,
    WashCategory, UserItem, Shop, Review, Timeslot, Booking,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'image', 'price', 'count']
        read_only_fields = ['id', 'count']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        fields = ['id', 'name', 'extra_per_item']
        read_only_fields = ['id']


class UserItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserItem
        fields = ['id', 'item', 'quantity', 'wash_category', 'price']
        read_only_fields = ['id', 'user', 'price']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        exclude = ['created_at', 'updated_at', 'user']
        read_only_fields = ['id']


class ShopReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['created_at', 'updated_at', 'user']
        read_only_fields = ['id']


class TimeslotQuerySerializer(serializers.Serializer):
    start_datetime = serializers.DateTimeField()
    end_datetime = serializers.DateTimeField()


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'time_slot', 'user', 'booking_type']
        read_only_fields = ['id']


class BookingRequestSerializer(serializers.Serializer):
    timeslot_id = serializers.IntegerField()
    booking_type = serializers.ChoiceField(
        choices=[(BookingType.PICK_UP.value, 'pick_up'), (BookingType.DELIVERY.value, 'delivery')])

    def validate(self, attrs):
        timeslot_id = attrs.get('timeslot_id')
        booking_type = attrs.get('booking_type')

        # Perform validation logic
        if not timeslot_id:
            raise serializers.ValidationError("timeslot_id is required.")
        if not booking_type:
            raise serializers.ValidationError("booking_type is required.")

        # Validate booking_type against BookingType enum
        try:
            booking_type = BookingType(booking_type)
        except ValueError:
            raise serializers.ValidationError("Invalid booking_type.")

        # Validate timeslot_id against existing Timeslot objects
        try:
            timeslot = Timeslot.objects.get(id=timeslot_id)
        except Timeslot.DoesNotExist:
            raise serializers.ValidationError("Invalid timeslot_id.")

        return attrs
