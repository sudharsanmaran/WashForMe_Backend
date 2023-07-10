""""
Serializer for user.
"""
from rest_framework import serializers

from core.models import Address, User


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ['user']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        address_type = data['type']
        is_primary = data['is_primary']

        if is_primary and Address.objects.filter(user=user, type=address_type, is_primary=True).exists():
            raise serializers.ValidationError("There is already a primary address with the same type.")

        return data


class UserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'other_details', 'is_phone_verified',
                  'cart_total_price', 'address']
        read_only_fields = ['id', 'is_phone_verified', 'cart_total_price', 'address']
