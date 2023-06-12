"""
Views for the
"""
import random

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token

from django.contrib.auth import get_user_model
from core import models
from core.api.serializers import (
    login_serializers,
    user_serializer,
)
from twilio.rest import Client

from WashForMe_Backend import settings


def generate_otp():
    return str(random.randint(1000, 9999))


class CreateOTPView(APIView):
    """Generate otp and stores in phone number table."""
    serializer_class = login_serializers.CreateOTPSerializer
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def get_or_create_phone_number(phone):
        try:
            phone_number_manager = models.PhoneNumberManager.objects.get(phone=phone)
            count = phone_number_manager.count + 1
        except ObjectDoesNotExist:
            phone_number_manager = models.PhoneNumberManager.objects.create(phone=phone, otp=generate_otp(), count=1)
            count = 1
        return phone_number_manager.otp, count

    @staticmethod
    def send_otp(phone, otp):
        # Send otp with twilio account.

        message = f'Your OTP is {otp}.'
        client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        return message

    @staticmethod
    def update_phone_number(otp, count, phone, message):
        # Update phone number model.

        try:
            phone_number_manager = models.PhoneNumberManager.objects.get(phone=phone)
            phone_number_manager.otp = otp
            phone_number_manager.count = count
            phone_number_manager.session_id = message.sid
            # serializer = serializers.CreateOTPSerializer(phone_number_manager)
            phone_number_manager.save()
        except ObjectDoesNotExist:
            pass

    def post(self, request):
        phone = request.data.get('phone')
        otp, count = self.get_or_create_phone_number(phone)

        if count >= 5:
            return Response({'error': 'Maximum limit reached.'}, status=status.HTTP_400_BAD_REQUEST)

        message = self.send_otp(phone, otp)
        self.update_phone_number(otp, count, phone, message)

        return Response({'message': 'OTP sent successfully.'})


class LoginOTPView(APIView):
    """Login OTP API View."""

    serializer_class = login_serializers.LoginOTPSerializer
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def get_phone_number_manager(phone):
        try:
            return models.PhoneNumberManager.objects.get(phone__iexact=phone)
        except models.PhoneNumberManager.DoesNotExist:
            return None

    @staticmethod
    def str_to_int(str_number: str) -> int:
        return int(str_number) if str_number.isnumeric else str_number

    def post(self, request) -> Response:
        phone = request.data.get('phone')
        otp = self.str_to_int(request.data.get('otp'))

        phone_number_manager = self.get_phone_number_manager(phone)

        if not phone_number_manager:
            return Response({'error': f'Generate otp for {phone} first.'})

        if phone_number_manager.otp != otp:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_user_model().objects.get(phone=phone)
        except models.User.DoesNotExist:
            user = get_user_model().objects.create_user(phone=phone)

        token, _ = Token.objects.get_or_create(user=user)

        response_data = {
            'token': token.key,
            'user': user_serializer.UserSerializer(user).data
        }
        phone_number_manager.delete()
        return Response(response_data)
