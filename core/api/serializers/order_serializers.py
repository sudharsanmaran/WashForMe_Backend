from rest_framework import serializers

from core.constants import OrderStatus
from core.models import OrderDetails, Order


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
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_price', 'user', 'order_status']

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

        order = Order.objects.create(user=user, order_status=OrderStatus.INITIATED.name, **validated_data)

        total_price = OrderSerializer.create_order_details(order, order_details_data)

        order.total_price = total_price
        order.save()
        return order

    def update(self, instance, validated_data):
        order_details_data = validated_data.pop('order_details') if 'order_details' in validated_data else None
        user = self.context['request'].user

        instance.user = user
        instance.pickup_booking = validated_data.get('pickup_booking', instance.pickup_booking)
        instance.delivery_booking = validated_data.get('delivery_booking', instance.delivery_booking)
        instance.save()

        if order_details_data:
            OrderDetails.objects.filter(order=instance).delete()
            total_price = OrderSerializer.create_order_details(instance, order_details_data)
            instance.total_price = total_price
            instance.save()

        return instance


class CartToOrderRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['pickup_booking', 'delivery_booking']
