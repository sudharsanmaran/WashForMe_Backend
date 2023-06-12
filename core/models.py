"""
Model in the app
"""
import phonenumbers as phonenumbers
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


from WashForMe_Backend import settings


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
    email = models.EmailField(max_length=255, unique=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    dictionary = dict(availability='Yes', notifications='On', language='English', dark_mode='No')
    other_details = models.TextField(default=dictionary, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'phone'

    def __str__(self):
        return self.phone


class PhoneNumberManager(models.Model):
    phone = models.CharField(max_length=255, unique=True)
    otp = models.IntegerField()
    count = models.IntegerField(default=0)
    session_id = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.otp}'


class Item(models.Model):
    name = models.CharField(max_length=55, unique=True)
    image = models.FileField(upload_to='images/', blank=True)
    price = models.IntegerField()
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=55, unique=True)
    extra_per_item = models.IntegerField(default=0)
    items = models.ManyToManyField(Item, blank=True)

    def __str__(self):
        return self.name


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    pincode = models.IntegerField()
    type = models.CharField(max_length=255)
