"""
Serializers for our application.
"""

from rest_framework import serializers


class CreateOTPSerializer(serializers.Serializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()


class LoginOTPSerializer(serializers.Serializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()
    otp = serializers.CharField()

