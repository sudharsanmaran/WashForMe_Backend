"""
Test for models
"""
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    def test_create_user_with_phone_successful(self):
        """Test creating a user with a phone number successful."""
        phone = '+918886568119'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            phone=phone,
            password=password
        )

        # Validate email
        self.assertEqual(user.phone, phone)

        # Validate password
        self.assertTrue(user.check_password(password))

    def test_new_user_without_phone_raises_error(self):
        """Test that creating a user without a phone number raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            '+918886568119',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
