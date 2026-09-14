from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import admin
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.recipes.models import Recipe
from apps.common.backend.auth_backends import OIDCAuthBackend
from apps.users.admin import OIDCProviderAdmin, OIDCProviderAdminForm
from apps.users.models import OIDCIdentity, OIDCProvider, RecipeBookmark, RecipeList


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cook", password="secret123")
        self.recipe = Recipe.objects.create(title="Soup", status="published", servings=2)
        self.client.login(username="cook", password="secret123")

    def test_profile_requires_login_and_can_update_details(self):
        self.client.logout()
        response = self.client.get(reverse("users:profile"))
        self.assertRedirects(response, "/account/login/?next=/account/profile/")

        self.client.login(username="cook", password="secret123")
        response = self.client.post(reverse("users:profile"), {
            "action": "profile", "email": "jamie@example.com",
        })
        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jamie@example.com")

    def test_public_login_page_uses_account_login_and_supports_next(self):
        self.client.logout()
        response = self.client.get(reverse("users:login"), {"next": "/recipes/"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in locally")
        self.assertContains(response, 'name="next" value="/recipes/"')
        response = self.client.post(reverse("users:login"), {
            "username": "cook", "password": "secret123", "next": "/recipes/",
        })
        self.assertRedirects(response, "/recipes/")

    @override_settings(OIDC_ENABLED=True, OIDC_ALLOW_LOCAL_LOGIN=False)
    def test_public_login_page_lists_only_enabled_oidc_providers_when_local_login_disabled(self):
        OIDCProvider.objects.create(
            name="Google", slug="google", image_url="https://id.example.test/google.svg",
            client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo", enabled=True,
        )
        OIDCProvider.objects.create(
            name="Disabled", slug="disabled", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo", enabled=False,
        )
        self.client.logout()
        response = self.client.get(reverse("users:login"))
        self.assertContains(response, "OIDC providers")
        self.assertContains(response, "Google")
        self.assertContains(response, "google.svg")
        self.assertNotContains(response, "Disabled")
        self.assertNotContains(response, "Sign in locally")

    @override_settings(OIDC_ENABLED=True, OIDC_ALLOW_LOCAL_LOGIN=True)
    def test_public_login_page_explains_when_oidc_is_enabled_but_unconfigured(self):
        self.client.logout()
        response = self.client.get(reverse("users:login"))
        self.assertContains(response, "Local login")
        self.assertContains(response, "OIDC providers")
        self.assertContains(response, "No OIDC providers have been configured yet.")

    def test_user_can_toggle_bookmark_and_add_recipe_to_list(self):
        response = self.client.post(reverse("users:toggle_bookmark", args=[self.recipe.slug]))
        self.assertRedirects(response, f"/recipes/{self.recipe.slug}/")
        self.assertTrue(RecipeBookmark.objects.filter(user=self.user, recipe=self.recipe).exists())

        recipe_list = RecipeList.objects.create(user=self.user, name="Favourites")
        self.client.post(reverse("users:add_to_list", args=[self.recipe.slug]), {"list_id": recipe_list.pk})
        response = self.client.get(reverse("users:recipe_list_detail", args=[recipe_list.pk]))
        self.assertContains(response, "Remove from list")
        self.assertContains(response, self.recipe.title)
        self.assertTrue(recipe_list.recipes.filter(pk=self.recipe.pk).exists())

    def test_recipe_detail_can_create_list_and_populated_lists_cannot_be_deleted(self):
        response = self.client.post(
            reverse("users:update_recipe_lists", args=[self.recipe.slug]),
            {"new_list_name": "Weeknight", "next": reverse("recipes:recipe_detail", args=[self.recipe.slug])},
        )
        self.assertRedirects(response, reverse("recipes:recipe_detail", args=[self.recipe.slug]))
        recipe_list = RecipeList.objects.get(user=self.user, name="Weeknight")
        self.assertTrue(recipe_list.recipes.filter(pk=self.recipe.pk).exists())

        response = self.client.post(reverse("users:delete_recipe_list", args=[recipe_list.pk]))
        self.assertRedirects(response, reverse("users:profile"))
        self.assertTrue(RecipeList.objects.filter(pk=recipe_list.pk).exists())

    def test_oidc_provider_login_stores_provider_selection(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo",
        )
        response = self.client.get(reverse("users:oidc_login", args=[provider.slug]), {"link": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["oidc_provider_slug"], provider.slug)
        self.assertEqual(self.client.session["oidc_link_user_id"], self.user.pk)

    def test_oidc_login_discards_external_next_url(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo",
        )
        response = self.client.get(reverse("users:oidc_login", args=[provider.slug]), {"next": "https://evil.example/"})
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session["oidc_login_next"])

    def test_recipe_mutation_redirects_reject_external_next_urls(self):
        recipe_list = RecipeList.objects.create(user=self.user, name="Dinner")
        endpoints = [
            (reverse("users:toggle_bookmark", args=[self.recipe.slug]), {}),
            (reverse("users:add_to_list", args=[self.recipe.slug]), {"list_id": recipe_list.pk}),
            (reverse("users:update_recipe_lists", args=[self.recipe.slug]), {"list_ids": [recipe_list.pk]}),
        ]

        for endpoint, data in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, {**data, "next": "https://evil.example/"})
                self.assertTrue(response.url.startswith("/recipes/"))
                self.assertNotIn("evil.example", response.url)

    def test_oidc_client_secret_uses_password_widget_and_is_not_rendered(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="super-secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo",
        )
        form = OIDCProviderAdminForm(instance=provider)

        self.assertEqual(form.fields["client_secret"].widget.input_type, "password")
        self.assertNotIn("super-secret", form.as_p())
        changed = OIDCProviderAdminForm({"name": provider.name, "slug": provider.slug, "client_id": provider.client_id,
                                         "authorization_endpoint": provider.authorization_endpoint,
                                         "token_endpoint": provider.token_endpoint, "userinfo_endpoint": provider.userinfo_endpoint,
                                         "scopes": provider.scopes, "signing_algorithm": provider.signing_algorithm,
                                         "enabled": provider.enabled, "authoritative": provider.authoritative,
                                         "auto_create_users": provider.auto_create_users, "staff_groups_claim": provider.staff_groups_claim,
                                         "staff_groups": provider.staff_groups}, instance=provider)
        self.assertTrue(changed.is_valid())
        self.assertEqual(changed.cleaned_data["client_secret"], "super-secret")

    def test_oidc_identity_can_be_unlinked_but_last_unusable_login_is_protected(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo",
        )
        identity = OIDCIdentity.objects.create(user=self.user, provider=provider, subject="subject")
        response = self.client.post(reverse("users:oidc_unlink", args=[provider.slug]))
        self.assertRedirects(response, reverse("users:profile"))
        self.assertTrue(OIDCIdentity.objects.filter(pk=identity.pk).exists())

        second_provider = OIDCProvider.objects.create(
            name="Google", slug="google", client_id="client", client_secret="secret",
            authorization_endpoint="https://accounts.example.test/auth", token_endpoint="https://accounts.example.test/token",
            userinfo_endpoint="https://accounts.example.test/userinfo",
        )
        second_identity = OIDCIdentity.objects.create(user=self.user, provider=second_provider, subject="other-subject")
        self.client.post(reverse("users:oidc_unlink", args=[provider.slug]))
        self.assertFalse(OIDCIdentity.objects.filter(pk=identity.pk).exists())
        self.assertTrue(OIDCIdentity.objects.filter(pk=second_identity.pk).exists())

    def test_admin_exposes_one_readonly_callback_and_connection_setup(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo", scopes="openid email groups",
        )
        request = RequestFactory().get("/admin/")
        request.META["HTTP_HOST"] = "testserver"
        admin_view = OIDCProviderAdmin(OIDCProvider, admin.site)
        admin_view._admin_request = request
        callback = admin_view.callback_url(provider)
        self.assertEqual(callback, "http://testserver/oidc/callback/")
        self.assertEqual(admin_view.required_scopes(provider), "openid email groups")
        self.assertIn("Authorization Code", str(admin_view.authorization_flow(provider)))
        self.assertIn("callback URL", str(admin_view.setup_instructions(provider)))

    def test_mounted_admin_site_exposes_oidc_provider_setup(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin-user", email="admin@example.com", password="admin-secret123"
        )
        self.client.force_login(admin_user)
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo",
        )
        index = self.client.get("/admin/")
        self.assertEqual(index.status_code, 200)
        self.assertContains(index, "OIDC providers")
        change = self.client.get(f"/admin/users/oidcprovider/{provider.pk}/change/")
        self.assertEqual(change.status_code, 200)
        self.assertContains(change, "Callback URL")
        self.assertContains(change, "/oidc/callback/")

    def test_authoritative_provider_syncs_staff_access_and_groups(self):
        provider = OIDCProvider.objects.create(
            name="Keycloak", slug="keycloak", client_id="client", client_secret="secret",
            authorization_endpoint="https://id.example.test/auth", token_endpoint="https://id.example.test/token",
            userinfo_endpoint="https://id.example.test/userinfo", authoritative=True,
            staff_groups="admins",
        )
        Group.objects.create(name="admins")
        Group.objects.create(name="unconfigured")
        backend = OIDCAuthBackend.__new__(OIDCAuthBackend)
        backend.provider = provider

        backend.update_user(self.user, {"email": self.user.email, "groups": ["admins", "unconfigured"]})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
        self.assertEqual(list(self.user.groups.values_list("name", flat=True)), ["admins"])

        backend.update_user(self.user, {"email": self.user.email, "groups": []})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.groups.exists())
