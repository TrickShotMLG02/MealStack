from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import resolve

from apps.common.backend.auth_backends import OIDCAuthBackend
from apps.common.text_formatting import slugify
from apps.recipes.models import Tag


class ReleaseConfigurationTests(SimpleTestCase):
    def test_admin_importer_overview_urls_resolve_to_custom_views(self):
        self.assertEqual(resolve("/admin/importers/").url_name, "importers_home")
        self.assertEqual(resolve("/admin/importers/ingredient/").url_name, "ingredient_importers_home")
        self.assertEqual(resolve("/admin/importers/recipe/").url_name, "recipe_importers_home")

    def test_i18n_context_processor_is_enabled(self):
        context_processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        self.assertIn("django.template.context_processors.i18n", context_processors)

    def test_slug_generation_normalizes_german_characters_for_urls(self):
        self.assertEqual(slugify("K\u00e4se \u00d6l s\u00fc\u00df"), "kaese-oel-suess")


class SeedCommandTests(TestCase):
    def test_seed_tags_does_not_delete_existing_tags(self):
        custom_tag = Tag.objects.create(name="Private", slug="private")

        call_command("seed_tags", verbosity=0)

        self.assertTrue(Tag.objects.filter(pk=custom_tag.pk, name="Private").exists())


class OIDCBackendTests(TestCase):
    def test_create_user_does_not_grant_staff_or_superuser(self):
        user = get_user_model().objects.create_user(
            username="person@example.com",
            email="person@example.com",
            is_staff=True,
            is_superuser=True,
        )
        backend = OIDCAuthBackend.__new__(OIDCAuthBackend)
        backend.create_user = OIDCAuthBackend.create_user.__get__(backend, OIDCAuthBackend)
        parent_create_user = OIDCAuthBackend.__mro__[1].create_user

        try:
            OIDCAuthBackend.__mro__[1].create_user = lambda _backend, _claims: user
            created_user = backend.create_user({"email": "person@example.com"})
        finally:
            OIDCAuthBackend.__mro__[1].create_user = parent_create_user

        self.assertFalse(created_user.is_superuser)
        self.assertFalse(created_user.is_staff)

    def test_update_user_preserves_existing_superuser_and_staff_flags(self):
        user = get_user_model().objects.create_user(
            username="admin",
            email="old@example.com",
            password="unused",
            is_superuser=True,
            is_staff=False,
        )

        backend = OIDCAuthBackend.__new__(OIDCAuthBackend)
        updated_user = backend.update_user(user, {"email": "admin@example.com"})

        self.assertTrue(updated_user.is_superuser)
        self.assertFalse(updated_user.is_staff)
        self.assertEqual(updated_user.email, "admin@example.com")

    def test_update_user_preserves_existing_staff_flag(self):
        user = get_user_model().objects.create_user(
            username="person",
            email="old@example.com",
            password="unused",
            is_superuser=False,
            is_staff=True,
        )

        backend = OIDCAuthBackend.__new__(OIDCAuthBackend)
        updated_user = backend.update_user(user, {"email": "person@example.com"})

        self.assertFalse(updated_user.is_superuser)
        self.assertTrue(updated_user.is_staff)
