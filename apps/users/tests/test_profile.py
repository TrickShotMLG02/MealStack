from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.recipes.models import Recipe
from apps.users.models import RecipeBookmark, RecipeList


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cook", password="secret123")
        self.recipe = Recipe.objects.create(title="Soup", status="published", servings=2)
        self.client.login(username="cook", password="secret123")

    def test_profile_requires_login_and_can_update_details(self):
        self.client.logout()
        response = self.client.get(reverse("users:profile"))
        self.assertRedirects(response, "/admin/login/?next=/account/profile/")

        self.client.login(username="cook", password="secret123")
        response = self.client.post(reverse("users:profile"), {
            "action": "profile", "email": "jamie@example.com",
        })
        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jamie@example.com")

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
