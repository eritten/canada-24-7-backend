from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser, OTPVerification


class AuthFlowTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_register_creates_unverified_user_and_otp(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Avery Laurent",
                "email": "avery@example.com",
                "password": "Canada247x9",
                "confirm_password": "Canada247x9",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email="avery@example.com")
        self.assertFalse(user.is_verified)
        self.assertTrue(OTPVerification.objects.filter(user=user, purpose=OTPVerification.PURPOSE_VERIFY).exists())

    def test_verify_email_returns_tokens(self):
        user = CustomUser.objects.create_user(email="avery@example.com", password="Canada247x9", full_name="Avery Laurent")
        otp = OTPVerification.objects.create(user=user, otp_code="123456", purpose=OTPVerification.PURPOSE_VERIFY)

        response = self.client.post("/api/auth/verify-email/", {"email": user.email, "otp_code": otp.otp_code}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertTrue(otp.is_used)
        self.assertIn("access", response.data["data"])


class PublicProfileTests(APITestCase):
    def test_guest_can_view_public_profile(self):
        user = CustomUser.objects.create_user(email="public@example.com", password="Canada247x9", full_name="Public User", is_verified=True)

        response = self.client.get(f"/api/profile/{user.profile.username}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["username"], user.profile.username)
