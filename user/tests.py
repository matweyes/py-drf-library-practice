from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

REGISTER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
REFRESH_URL = reverse("user:token_refresh")
ME_URL = reverse("user:manage")


def create_user(**params):
    defaults = {
        "email": "test@test.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        email = "user@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_email_normalized(self):
        emails = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@Example.COM", "Test2@example.com"),
            ("TEST3@EXAMPLE.COM", "TEST3@example.com"),
        ]
        for raw, expected in emails:
            user = get_user_model().objects.create_user(email=raw, password="test123")
            self.assertEqual(user.email, expected)

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="test123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(email="admin@example.com", password="admin123")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class PublicUserApiTests(TestCase):
    """Tests for unauthenticated user API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        payload = {"email": "new@example.com", "password": "newpass123"}
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_register_user_already_exists(self):
        create_user(email="existing@example.com")
        payload = {"email": "existing@example.com", "password": "testpass123"}
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short(self):
        payload = {"email": "short@example.com", "password": "pw"}
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.filter(email=payload["email"]).exists())

    def test_register_does_not_set_is_staff(self):
        payload = {"email": "hack@example.com", "password": "hackpass123", "is_staff": True}
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertFalse(user.is_staff)

    def test_token_returns_tokens(self):
        create_user(email="login@example.com", password="loginpass123")
        payload = {"email": "login@example.com", "password": "loginpass123"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_token_bad_credentials(self):
        create_user(email="login@example.com", password="loginpass123")
        payload = {"email": "login@example.com", "password": "wrongpass"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", res.data)

    def test_token_nonexistent_user(self):
        payload = {"email": "ghost@example.com", "password": "ghostpass"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        create_user(email="refresh@example.com", password="refreshpass123")
        login_res = self.client.post(TOKEN_URL, {"email": "refresh@example.com", "password": "refreshpass123"})
        refresh_token = login_res.data["refresh"]

        res = self.client.post(REFRESH_URL, {"refresh": refresh_token})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_refresh_token_invalid(self):
        res = self.client.post(REFRESH_URL, {"refresh": "invalid-token"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_auth_required(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Tests for authenticated user API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="auth@example.com", password="authpass123")
        self.client.force_authenticate(self.user)

    def test_retrieve_profile(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertEqual(res.data["id"], self.user.id)
        self.assertNotIn("password", res.data)

    def test_update_profile_email(self):
        res = self.client.patch(ME_URL, {"email": "updated@example.com"})

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.email, "updated@example.com")

    def test_update_profile_password(self):
        res = self.client.patch(ME_URL, {"password": "newpass123"})

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password("newpass123"))

    def test_update_profile_cannot_set_is_staff(self):
        self.client.patch(ME_URL, {"is_staff": True})

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_post_not_allowed_on_me(self):
        res = self.client.post(ME_URL, {"email": "new@example.com"})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed_on_me(self):
        res = self.client.delete(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
