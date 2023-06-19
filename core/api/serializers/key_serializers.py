"""
Key Serializers.
"""
from rest_framework import (
    serializers,
)

from core.models import (
    Item,
    WashCategory, Cart, Shop, Review, Timeslot, BookTimeslot, Payment, OrderDetails, Order,
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
        read_only_fields = ['id', 'created_at', 'order', 'product_price', 'wash_category_price',
                            'updated_at', 'subtotal_price']


class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_price', 'user', 'payment']

    @staticmethod
    def create_order_details(order, order_details_data):
        order_details, total_price = [], 0
        for order_detail_data in order_details_data:
            product_price = order_detail_data['product'].price
            wash_category_price = order_detail_data['wash_category'].extra_per_item

            subtotal_price = (product_price + wash_category_price) * order_detail_data['quantity']
            total_price += subtotal_price
            order_detail_data['subtotal_price'] = subtotal_price
            order_detail_data['product_price'] = product_price
            order_detail_data['wash_category_price'] = wash_category_price

            order_details.append(OrderDetails(order=order, **order_detail_data))
        OrderDetails.objects.bulk_create(order_details)
        return total_price

    def create(self, validated_data):
        order_details_data = validated_data.pop('order_details')
        user = self.context['request'].user

        order = Order.objects.create(user=user, **validated_data)

        total_price = OrderSerializer.create_order_details(order, order_details_data)

        order.total_price = total_price
        order.save()
        return order

    def update(self, instance, validated_data):
        order_details_data = validated_data.pop('order_details') if 'order_details' in validated_data else None
        user = self.context['request'].user

        instance.user = user
        instance.order_status = validated_data.get('order_status', instance.order_status)
        instance.pickup_booking = validated_data.get('pickup_booking', instance.pickup_booking)
        instance.delivery_booking = validated_data.get('delivery_booking', instance.delivery_booking)
        instance.payment = validated_data.get('payment', instance.payment)
        instance.save()

        if order_details_data:
            OrderDetails.objects.filter(order=instance).delete()
            total_price = OrderSerializer.create_order_details(instance, order_details_data)
            instance.total_price = total_price
            instance.save()

        return instance
