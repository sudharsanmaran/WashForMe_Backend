"""
Test cases for the user details.
"""
from unittest import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse


USER_URL = 'core:user-details'


class PublicUserAPITests(TestCase):
    """Test cases for checking user APIs in public."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_retrieving_user_details(self):
        """Test case for the retrieving user details."""

        res = self.client.get(USER_URL)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

