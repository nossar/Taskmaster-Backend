from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterViewTests(APITestCase):
    def test_register_creates_user_with_hashed_password(self) -> None:
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "alice",
                "email": "alice@example.com",
                "password": "xK9#mP2$vL8@nQ4!",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="alice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertNotEqual(user.password, "xK9#mP2$vL8@nQ4!")
        self.assertTrue(user.check_password("xK9#mP2$vL8@nQ4!"))

    def test_register_rejects_duplicate_username(self) -> None:
        User.objects.create_user("alice", "a@example.com", "sE7!kM2@nP9#xQ1")

        response = self.client.post(
            reverse("users:register"),
            {
                "username": "alice",
                "email": "other@example.com",
                "password": "xK9#mP2$vL8@nQ4!",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_weak_password(self) -> None:
        response = self.client.post(
            reverse("users:register"),
            {"username": "bob", "email": "bob@example.com", "password": "123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="bob").exists())


class LoginLogoutTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "carol", "carol@example.com", "sE7!kM2@nP9#xQ1"
        )

    def test_login_returns_access_and_refresh_tokens(self) -> None:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "carol", "password": "sE7!kM2@nP9#xQ1"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_logout_blacklists_refresh_token(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("users:logout"), {"refresh": str(refresh)}
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_response = self.client.post(
            reverse("token_refresh"), {"refresh": str(refresh)}
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self) -> None:
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            reverse("users:logout"), {"refresh": str(refresh)}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "dave", "dave@example.com", "sE7!kM2@nP9#xQ1"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.get(reverse("users:me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_view_own_data(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("users:me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "dave")
        self.assertEqual(response.data["email"], "dave@example.com")

    def test_authenticated_user_can_update_email(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("users:me"), {"email": "new-dave@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new-dave@example.com")

    def test_username_field_is_read_only(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.patch(reverse("users:me"), {"username": "hacker"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "dave")


class ChangePasswordViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "erin", "erin@example.com", "sE7!kM2@nP9#xQ1"
        )

    def test_unauthenticated_request_is_rejected(self) -> None:
        response = self.client.post(
            reverse("users:change_password"),
            {"current_password": "sE7!kM2@nP9#xQ1", "new_password": "nP9#xQ1!sE7@kM2"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_current_password_is_rejected(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("users:change_password"),
            {"current_password": "errada", "new_password": "nP9#xQ1!sE7@kM2"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("sE7!kM2@nP9#xQ1"))

    def test_correct_current_password_updates_password(self) -> None:
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("users:change_password"),
            {
                "current_password": "sE7!kM2@nP9#xQ1",
                "new_password": "nP9#xQ1!sE7@kM2",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("nP9#xQ1!sE7@kM2"))
        self.assertFalse(self.user.check_password("sE7!kM2@nP9#xQ1"))


class PasswordResetTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            "frank", "frank@example.com", "sE7!kM2@nP9#xQ1"
        )

    def test_request_with_known_email_sends_mail(self) -> None:
        response = self.client.post(
            reverse("users:password_reset"), {"email": "frank@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("frank@example.com", mail.outbox[0].to)

    def test_request_with_unknown_email_returns_generic_response(self) -> None:
        response = self.client.post(
            reverse("users:password_reset"), {"email": "ghost@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_with_valid_token_resets_password(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {"uid": uid, "token": token, "new_password": "nP9#xQ1!sE7@kM2"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("nP9#xQ1!sE7@kM2"))

    def test_confirm_with_invalid_token_is_rejected(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {"uid": uid, "token": "token-invalido", "new_password": "nP9#xQ1!sE7@kM2"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("sE7!kM2@nP9#xQ1"))
