from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.recipes.models import (
    Ingredient, Unit, Recipe, RecipeIngredient, RecipeStep, Tag, RecipeNutrition
)
from apps.recipes.services.nutrition import update_recipe_nutrition


class Command(BaseCommand):
    help = "Seed test recipes, ingredients, units, tags, and nutrition"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding ingredients...")
        sugar, _ = Ingredient.objects.get_or_create(
            name="Sugar", kcal=400, protein=0, fat=0, carbs=100, salt=0
        )
        milk, _ = Ingredient.objects.get_or_create(
            name="Milk", kcal=60, protein=3, fat=3, carbs=5, salt=0, density=1.03
        )
        egg, _ = Ingredient.objects.get_or_create(
            name="Egg", kcal=155, protein=13, fat=11, carbs=1, salt=0.1
        )

        self.stdout.write("Seeding tags...")
        dessert_tag, _ = Tag.objects.get_or_create(name="Dessert")
        breakfast_tag, _ = Tag.objects.get_or_create(name="Breakfast")

        self.stdout.write("Seeding recipe...")
        cake, _ = Recipe.objects.get_or_create(
            title="Test Cake", servings=2, status="draft", source="Seed Command"
        )

        # Add tags
        cake.tags.add(dessert_tag)

        self.stdout.write("Seeding recipe ingredients...")
        RecipeIngredient.objects.get_or_create(recipe=cake, ingredient=sugar, quantity=100, unit=gram)
        RecipeIngredient.objects.get_or_create(recipe=cake, ingredient=milk, quantity=200, unit=ml)
        RecipeIngredient.objects.get_or_create(recipe=cake, ingredient=egg, quantity=2, unit=piece)

        self.stdout.write("Seeding recipe steps...")
        RecipeStep.objects.get_or_create(recipe=cake, order=1, description="Mix sugar and eggs.")
        RecipeStep.objects.get_or_create(recipe=cake, order=2, description="Add milk and stir.")
        RecipeStep.objects.get_or_create(recipe=cake, order=3, description="Bake at 180°C for 25 minutes.")

        # Update nutrition using your service
        self.stdout.write("Calculating recipe nutrition...")
        update_recipe_nutrition(cake)

        self.stdout.write(self.style.SUCCESS("✅ Test data seeded successfully."))