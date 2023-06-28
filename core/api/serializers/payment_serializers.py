from rest_framework import serializers

from core.models import Payment, RazorpayPayment, Order


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RazorpayOrderResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    entity = serializers.CharField()
    amount = serializers.IntegerField()
    amount_paid = serializers.IntegerField()
    amount_due = serializers.IntegerField()
    currency = serializers.CharField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    notes = serializers.DictField()
    created_at = serializers.IntegerField()


class RazorpayPaymentInitiateResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer(read_only=True)
    razorpay = RazorpayOrderResponseSerializer(read_only=True)


class RazorpayPaymentRequestSerializer(serializers.ModelSerializer):
    payment_id = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
    class Meta:
        model = RazorpayPayment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'payment']


class RazorpayInitiateSerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())


class RazorpayPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazorpayPayment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RazorpayPartialPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazorpayPayment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'razorpay_signature', 'razorpay_payment_id']
