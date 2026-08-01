from django.db import models
from django.utils.translation import gettext_lazy as _


class RecipeNutrition(models.Model):
    recipe = models.OneToOneField('Recipe', on_delete=models.CASCADE, related_name='recipe_nutrition')

    # total values
    total_kcal = models.FloatField(default=0, verbose_name=_("Total kcal"))
    total_fat = models.FloatField(default=0, verbose_name=_("Total fat"))
    total_saturates = models.FloatField(default=0, verbose_name=_("Total saturates"))
    total_carbs = models.FloatField(default=0, verbose_name=_("Total carbs"))
    total_sugar = models.FloatField(default=0, verbose_name=_("Total sugar"))
    total_protein = models.FloatField(default=0, verbose_name=_("Total protein"))
    total_salt = models.FloatField(default=0, verbose_name=_("Total salt"))

    # per-serving
    per_serving_kcal = models.FloatField(default=0, verbose_name=_("Per serving kcal"))
    per_serving_fat = models.FloatField(default=0, verbose_name=_("Per serving fat"))
    per_serving_saturates = models.FloatField(default=0, verbose_name=_("Per serving saturates"))
    per_serving_carbs = models.FloatField(default=0, verbose_name=_("Per serving carbs"))
    per_serving_sugar = models.FloatField(default=0, verbose_name=_("Per serving sugar"))
    per_serving_protein = models.FloatField(default=0, verbose_name=_("Per serving protein"))
    per_serving_salt = models.FloatField(default=0, verbose_name=_("Per serving salt"))

    class Meta:
        verbose_name = _("Recipe Nutrition")
        verbose_name_plural = _("Recipe Nutritions")

    def __str__(self):
        return f"Nutrition for {self.recipe.title}"