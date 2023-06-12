""""
Serializer for user.
"""
from rest_framework import serializers
from core import models


class UserSerializer(serializers.ModelSerializer):
    """Serializer class for the user."""

    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'other_details']
        write_only_fields = ['first_name', 'last_name', 'email']
        read_only_fields = ['id']


class AddressSerializer(serializers.ModelSerializer):
    """Serializer class for the user address."""

    class Meta:
        model = models.Address
        fields = '__all__'
        read_only_fields = ['id', 'user']
