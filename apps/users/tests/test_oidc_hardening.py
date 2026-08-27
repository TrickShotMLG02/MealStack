from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
        self.assertTrue(query["redirect_uri"][0].endswith("/oidc/callback/"))
        self.assertEqual(self.client.session["oidc_provider_slug"], provider.slug)

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
