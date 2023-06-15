"""
Key Serializers.
"""
from rest_framework import (
    serializers,
)

from core.constants import BookingType
from core.models import (
    Item,
    WashCategory, Cart, Shop, Review, Timeslot, BookTimeslot, Address, Payment, OrderDetails, Order,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['id', 'count']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        fields = '__all__'
        read_only_fields = ['id']


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['id', 'user', 'price']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class ShopReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['created_at', 'updated_at', 'user']
        read_only_fields = ['id']


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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class OrderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_price',
                            'wash_category_price', 'subtotal_price']


class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_price', 'user']
