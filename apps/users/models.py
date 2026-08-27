from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class RecipeBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_bookmarks")
    recipe = models.ForeignKey("recipes.Recipe", on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="unique_user_recipe_bookmark")]
        verbose_name = _("Recipe bookmark")
        verbose_name_plural = _("Recipe bookmarks")


class RecipeList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_lists")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    recipes = models.ManyToManyField("recipes.Recipe", related_name="user_lists", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_user_recipe_list_name")]
        verbose_name = _("Recipe list")
        verbose_name_plural = _("Recipe lists")

    def __str__(self):
        return self.name
