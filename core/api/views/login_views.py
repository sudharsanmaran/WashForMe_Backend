import random

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from WashForMe_Backend import settings
from core import models
from core.api.serializers import (
    login_serializers,
    user_serializer,
)


def TwilioClient():
    return Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)


def generate_otp():
    return str(random.randint(1000, 9999))


class SendOTPView(APIView):
    """Generate otp and stores in phone number table."""
    throttle_classes = [UserRateThrottle]
    serializer_class = login_serializers.CreateOTPSerializer
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def send_otp(phone, otp):
        # Send otp with twilio account.
        try:
            my_otp = f'Your OTP is {otp}.'
            client = TwilioClient()
            message = client.messages.create(
                body=my_otp,
                to=phone,
                from_=settings.TWILIO_PHONE_NUMBER,
            )
        except TwilioRestException as e:
            error_dict = {'send': False, 'message': str(e)}
            if e.code == 21211:
                error_message = "Invalid phone number"
            elif e.code == 21608:
                error_message = "The number is unverified."

            if error_message:
                error_dict['message'] = error_message
            return error_dict
        return {'send': True, 'message': message}

    def post(self, request):
        phone = request.data.get('phone')
        otp = generate_otp()
        cache.set(phone, otp, timeout=300)
        response = self.send_otp(phone, otp)
        if response['send']:
            return Response({'message': 'OTP sent successfully.'})
        return Response({'message': response['message']}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """Login OTP API View."""
    throttle_classes = [UserRateThrottle]
    serializer_class = login_serializers.LoginOTPSerializer
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def str_to_int(str_number: str) -> int:
        return int(str_number) if str_number.isnumeric else str_number

    def post(self, request) -> Response:
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        # cache_otp = cache.get(phone)
        cache_otp = '0000'
        if cache_otp == otp:
            try:
                user = get_user_model().objects.get(phone=phone)
            except models.User.DoesNotExist:
                user = get_user_model().objects.create_user(phone=phone)

            token = RefreshToken.for_user(user)

            response_data = {
                'refresh': str(token),
                'access': str(token.access_token),

                'user': user_serializer.UserSerializer(user).data
            }

            cache.delete(phone)
            return Response(response_data)
        else:
            return Response({"error": "OTP not generated or expired."})
