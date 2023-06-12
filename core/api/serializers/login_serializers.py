from rest_framework import serializers

class CreateOTPSerializer(serializers.Serializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()


class LoginOTPSerializer(serializers.Serializer):
    """Serializer for creating otp."""
    phone = serializers.CharField()
    otp = serializers.CharField()



class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()
