from django.db import models


class RecipeNutrition(models.Model):
    recipe = models.OneToOneField('Recipe', on_delete=models.CASCADE, related_name='recipe_nutrition')

    # total values
    total_kcal = models.FloatField(default=0)
    total_protein = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_salt = models.FloatField(default=0)

    # per-serving
    per_serving_kcal = models.FloatField(default=0)
    per_serving_protein = models.FloatField(default=0)
    per_serving_fat = models.FloatField(default=0)
    per_serving_carbs = models.FloatField(default=0)
    per_serving_salt = models.FloatField(default=0)

    def __str__(self):
        return f"Nutrition for {self.recipe.title}"