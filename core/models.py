import uuid
from datetime import timedelta, time

import phonenumbers as phonenumbers
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from WashForMe_Backend import settings
from core.constants import PaymentSource, PaymentStatus, OrderStatus, BookingType, AddressType
from core.custom_model_fields import PositiveDecimalField, CustomPositiveInteger


class UserManager(BaseUserManager):
    """Customized UserManager"""

    def create_user(self, phone, password=None, **extra_fields):
        """Create, save and returns a user."""
        if not phone or phone.isalpha():
            raise ValueError('Phone number must be number.')
        elif not phonenumbers.is_valid_number(phonenumbers.parse(phone)):
            raise ValueError('Phone number is not valid.')
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)

        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """Create, save and returns a superuser."""
        user = self.create_user(phone, password, **extra_fields)

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Customized user model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    dictionary = dict(availability='Yes', notifications='On', language='English', dark_mode='No')
    other_details = models.TextField(default=dictionary, blank=True)
    cart_total_price = PositiveDecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'phone'

    def __str__(self):
        return self.phone


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=55, unique=True)
    image = models.FileField(upload_to='images/', blank=True)
    price = PositiveDecimalField(max_digits=10, decimal_places=2, default=0.0)
    count = models.IntegerField(default=0)
    extras = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WashCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=55, unique=True)
    extra_per_item = PositiveDecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='address'
    )
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    pincode = models.IntegerField(default=000000)
    type = models.CharField(max_length=20,
                            choices=[(tag.name, tag.value) for tag in AddressType])
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('type', 'is_primary')]


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    wash_category = models.ForeignKey(WashCategory, on_delete=models.CASCADE)
    quantity = CustomPositiveInteger(default=1)
    price = PositiveDecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Shop(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    time_zone_offset = models.IntegerField(default=330)  # +5:30 offset from UTC
    wash_duration = models.DurationField(default=timedelta(days=2),
                                         validators=[MinValueValidator(timedelta(days=1))])
    time_slot_duration = models.DurationField(default=timedelta(hours=3),
                                              validators=[MinValueValidator(timedelta(hours=1))])
    active = models.BooleanField(default=True)
    max_user_limit_per_time_slot = CustomPositiveInteger(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Timeslot(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    pickup_available_quota = models.PositiveIntegerField()
    delivery_available_quota = models.PositiveIntegerField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    class Meta:
        ordering = ['shop', 'start_datetime']


class BookTimeslot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_slot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=20,
                                    choices=[(tag.name, tag.value) for tag in BookingType])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pickup_booking = models.OneToOneField(BookTimeslot, on_delete=models.CASCADE, related_name='pickup_orders')
    delivery_booking = models.OneToOneField(BookTimeslot, on_delete=models.CASCADE, related_name='delivery_orders')
    total_price = PositiveDecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    order_status = models.CharField(max_length=20,
                                    choices=[(tag.name, tag.value) for tag in OrderStatus])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_details')
    product = models.ForeignKey(Item, on_delete=models.CASCADE)
    wash_category = models.ForeignKey(WashCategory, on_delete=models.CASCADE)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    wash_category_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal_price = PositiveDecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = PositiveDecimalField(max_digits=10, decimal_places=2)
    payment_source = models.CharField(max_length=20,
                                      choices=[(tag.name, tag.value) for tag in PaymentSource])
    payment_status = models.CharField(max_length=20,
                                      choices=[(tag.name, tag.value) for tag in PaymentStatus])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RazorpayPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
