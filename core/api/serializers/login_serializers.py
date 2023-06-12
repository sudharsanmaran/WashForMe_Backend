"""
Serializers for our application.
"""

from rest_framework import serializers
from core import models


class CreateOTPSerializer(serializers.ModelSerializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()

    class Meta:
        model = models.PhoneNumberManager
        fields = '__all__'
        read_only_fields = ['otp', 'count', 'session_id']


class LoginOTPSerializer(serializers.ModelSerializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()
    otp = serializers.CharField()

    class Meta:
        model = models.PhoneNumberManager
        fields = '__all__'
        read_only_fields = ['count', 'session_id']
