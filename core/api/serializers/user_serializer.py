""""
Serializer for user.
"""
from rest_framework import serializers

from core.models import Address, User


class AddressSerializer(serializers.ModelSerializer):
    """Serializer class for the user address."""

    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['id', 'user']


class UserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'other_details', 'is_phone_verified',
                  'cart_total_price', 'address']
        read_only_fields = ['id', 'is_phone_verified', 'cart_total_price']
