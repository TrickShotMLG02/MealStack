import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from mozilla_django_oidc.utils import generate_code_challenge
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from unittest.mock import patch

from apps.common.backend.auth_backends import OIDCAuthBackend
from apps.users.models import OIDCIdentity, OIDCProvider


def make_provider(index, **overrides):
    values = {
        "name": f"Provider {index}",
        "slug": f"provider-{index}",
        "client_id": f"client-{index}",
        "client_secret": "test-secret",
        "authorization_endpoint": "https://id.example.test/authorize",
        "token_endpoint": "https://id.example.test/token",
        "userinfo_endpoint": "https://id.example.test/userinfo",
        "scopes": "openid email profile",
    }
    values.update(overrides)
    return OIDCProvider.objects.create(**values)


class OIDCAuthorizationHardeningTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="oidc-user", password="secret123")
        self.client.force_login(self.user)


def _authorization_test(index):
    def test(self):
        scopes = [
            "openid", "openid email", "openid profile", "openid email profile",
            "openid email groups", "openid profile groups", "openid email profile groups",
            "openid address", "openid phone", "openid email profile offline_access",
        ][index % 10]
        provider = make_provider(index, scopes=scopes)
        response = self.client.get(reverse("users:oidc_login", args=[provider.slug]))
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(query["client_id"], [provider.client_id])
        self.assertEqual(query["scope"], [scopes])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(len(query["state"][0]), 32)
        self.assertEqual(len(query["nonce"][0]), 32)
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertTrue(query["code_challenge"][0])
        self.assertTrue(query["redirect_uri"][0].endswith("/oidc/callback/"))
        self.assertEqual(self.client.session["oidc_provider_slug"], provider.slug)
        state_data = self.client.session["oidc_states"][query["state"][0]]
        self.assertEqual(len(state_data["code_verifier"]), 64)

    return test


for _index in range(50):
    setattr(OIDCAuthorizationHardeningTests, f"test_authorization_request_matrix_{_index:02d}", _authorization_test(_index))


class OIDCUnlinkHardeningTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="unlink-user", password="secret123")
        self.client.force_login(self.user)


def _final_identity_test(index):
    def test(self):
        provider = make_provider(100 + index)
        identity = OIDCIdentity.objects.create(user=self.user, provider=provider, subject=f"subject-{index}")
        response = self.client.post(reverse("users:oidc_unlink", args=[provider.slug]))
        self.assertRedirects(response, reverse("users:profile"))
        self.assertTrue(OIDCIdentity.objects.filter(pk=identity.pk).exists())

    return test


for _index in range(50):
    setattr(OIDCUnlinkHardeningTests, f"test_final_oidc_identity_is_protected_{_index:02d}", _final_identity_test(_index))


class OIDCIdentityAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="linked-user", email="linked@example.com")
        self.other_user = get_user_model().objects.create_user(username="other-user", email="linked@example.com")
        self.provider = make_provider(200, issuer="https://id.example.test", signing_algorithm="HS256")

    def backend(self, session=None):
        backend = OIDCAuthBackend.__new__(OIDCAuthBackend)
        backend.provider = self.provider
        backend.UserModel = get_user_model()
        backend.request = SimpleNamespace(session=session or {}, user=self.user)
        backend.get_userinfo = lambda access_token, id_token, payload: {
            "sub": payload["sub"],
            "email": "linked@example.com",
            "email_verified": True,
        }
        return backend

    def test_unlinked_provider_identity_cannot_log_in_by_email(self):
        backend = self.backend()

        result = backend.get_or_create_user(None, None, {"sub": "unlinked-sub"})

        self.assertIsNone(result)

    def test_linking_existing_identity_belonging_to_other_user_is_rejected(self):
        OIDCIdentity.objects.create(user=self.other_user, provider=self.provider, subject="existing-sub")
        backend = self.backend({"oidc_link_user_id": self.user.pk})

        result = backend.get_or_create_user(None, None, {"sub": "existing-sub"})

        self.assertIsNone(result)
        self.assertEqual(OIDCIdentity.objects.get(provider=self.provider, subject="existing-sub").user_id, self.other_user.pk)

    def test_linking_new_identity_belongs_to_current_user(self):
        backend = self.backend({"oidc_link_user_id": self.user.pk})

        result = backend.get_or_create_user(None, None, {"sub": "new-sub"})

        self.assertEqual(result, self.user)
        self.assertTrue(OIDCIdentity.objects.filter(user=self.user, provider=self.provider, subject="new-sub").exists())

    def test_linking_existing_identity_for_same_user_is_idempotent(self):
        identity = OIDCIdentity.objects.create(user=self.user, provider=self.provider, subject="same-sub")
        backend = self.backend({"oidc_link_user_id": self.user.pk})

        result = backend.get_or_create_user(None, None, {"sub": "same-sub"})

        self.assertEqual(result, self.user)
        self.assertEqual(OIDCIdentity.objects.filter(provider=self.provider, subject="same-sub").count(), 1)
        self.assertEqual(OIDCIdentity.objects.get(pk=identity.pk).user_id, self.user.pk)

    def test_linking_requires_the_current_request_to_be_authenticated(self):
        backend = self.backend({"oidc_link_user_id": self.user.pk})
        backend.request.user = AnonymousUser()

        result = backend.get_or_create_user(None, None, {"sub": "anonymous-link"})

        self.assertIsNone(result)
        self.assertFalse(OIDCIdentity.objects.filter(subject="anonymous-link").exists())

    def test_already_linked_identity_can_authenticate_normally(self):
        OIDCIdentity.objects.create(user=self.user, provider=self.provider, subject="linked-sub")
        backend = self.backend()

        result = backend.get_or_create_user(None, None, {"sub": "linked-sub"})

        self.assertEqual(result, self.user)

    def test_claims_require_subject_and_verified_email(self):
        backend = self.backend()

        self.assertFalse(backend.verify_claims({"email": "linked@example.com", "email_verified": True}))
        self.assertFalse(backend.verify_claims({"sub": "subject", "email": "linked@example.com", "email_verified": False}))
        self.assertTrue(backend.verify_claims({"sub": "subject", "email": "linked@example.com", "email_verified": True}))
        self.assertTrue(backend.verify_claims({"sub": "subject"}))
        for invalid_subject in ("", "   ", None, 123, []):
            self.assertFalse(backend.verify_claims({"sub": invalid_subject}))

    def test_pkce_challenge_matches_saved_verifier(self):
        provider = make_provider(201)
        response = self.client.get(reverse("users:oidc_login", args=[provider.slug]))
        query = parse_qs(urlparse(response["Location"]).query)
        verifier = self.client.session["oidc_states"][query["state"][0]]["code_verifier"]

        self.assertEqual(query["code_challenge"][0], generate_code_challenge(verifier, "S256"))

    def test_jwt_requires_expected_issuer_and_audience(self):
        backend = self.backend()
        claims = {
            "sub": "subject",
            "iss": self.provider.issuer,
            "aud": self.provider.client_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,
        }

        valid = jwt.encode(claims, self.provider.client_secret, algorithm="HS256")
        self.assertEqual(backend._verify_jws(valid, self.provider.client_secret)["sub"], "subject")

        for changed_claim in ({"iss": "https://evil.example.test"}, {"aud": "another-client"}):
            invalid_claims = {**claims, **changed_claim}
            token = jwt.encode(invalid_claims, self.provider.client_secret, algorithm="HS256")
            with self.assertRaises(SuspiciousOperation):
                backend._verify_jws(token, self.provider.client_secret)

        invalid_tokens = [
            jwt.encode({**claims, "exp": int(time.time()) - 1}, self.provider.client_secret, algorithm="HS256"),
            jwt.encode({**claims, "aud": [self.provider.client_id, "another-client"]}, self.provider.client_secret, algorithm="HS256"),
            jwt.encode({**claims, "aud": [self.provider.client_id, "another-client"], "azp": "another-client"}, self.provider.client_secret, algorithm="HS256"),
            jwt.encode(claims, self.provider.client_secret, algorithm="HS384"),
        ]
        for token in invalid_tokens:
            with self.assertRaises(SuspiciousOperation):
                backend._verify_jws(token, self.provider.client_secret)

    def test_jwt_requires_provider_issuer(self):
        backend = self.backend()
        backend.provider.issuer = ""
        claims = {
            "sub": "subject",
            "iss": "https://id.example.test",
            "aud": self.provider.client_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,
        }
        token = jwt.encode(claims, self.provider.client_secret, algorithm="HS256")

        with self.assertRaises(SuspiciousOperation):
            backend._verify_jws(token, self.provider.client_secret)


class OIDCCallbackCleanupTests(TestCase):
    def _request_with_flow_state(self):
        class TestSession(dict):
            def save(self):
                pass

        session = TestSession({"oidc_provider_slug": "provider", "oidc_link_user_id": 42,
                               "oidc_login_next": "/recipes/", "oidc_states": {"state": {}}})
        return SimpleNamespace(session=session)

    def test_callback_clears_flow_state_after_success(self):
        from apps.common.oidc_views import MealStackOIDCCallbackView

        request = self._request_with_flow_state()
        with patch.object(OIDCAuthenticationCallbackView, "get", return_value=HttpResponseRedirect("/")):
            MealStackOIDCCallbackView().get(request)

        self.assertFalse(any(key.startswith("oidc_") for key in request.session))

    def test_callback_clears_flow_state_after_exception(self):
        from apps.common.oidc_views import MealStackOIDCCallbackView

        request = self._request_with_flow_state()
        with patch.object(OIDCAuthenticationCallbackView, "get", side_effect=RuntimeError("callback failed")):
            with self.assertRaises(RuntimeError):
                MealStackOIDCCallbackView().get(request)

        self.assertFalse(any(key.startswith("oidc_") for key in request.session))
