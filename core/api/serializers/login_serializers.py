import phonenumbers
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class CreateOTPSerializer(serializers.Serializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get('phone')
        try:
            if not phonenumbers.is_valid_number(phonenumbers.parse(phone)):
                raise ValidationError('phone number is not valid')
        except Exception as e:
            raise ValidationError({'phone': 'phone number is not valid'})

        return attrs


class LoginOTPSerializer(CreateOTPSerializer):
    """Serializer for creating otp."""
    otp = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()
