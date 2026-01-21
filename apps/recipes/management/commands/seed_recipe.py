from apps.recipes.models import Recipe, RecipeIngredient, Tag, Ingredient, Unit, RecipeStep
from apps.recipes.services.nutrition import update_recipe_nutrition
from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial units"

    def get_seed_name(self):
        return "Units"


    def seed(self, *args, **kwargs):
        # get existing tags
        dessert_tag = Tag.objects.get(name="Dessert")

        # get existing ingredients
        sugar = Ingredient.objects.get(name="Sugar")
        milk = Ingredient.objects.get(name="Milk")
        egg = Ingredient.objects.get(name="Egg")

        # get existing units
        gram = Unit.objects.get(name="gram")
        ml = Unit.objects.get(name="ml")
        piece = Unit.objects.get(name="piece")

        # create recipe
        cake, _ = Recipe.objects.create(
            title="Test Cake", servings=2, status="draft", source="Seed Command"
        )
        cake.tags.add(dessert_tag)

        RecipeIngredient.objects.create(recipe=cake, ingredient=sugar, quantity=100, unit=gram)
        RecipeIngredient.objects.create(recipe=cake, ingredient=milk, quantity=200, unit=ml)
        RecipeIngredient.objects.create(recipe=cake, ingredient=egg, quantity=2, unit=piece)

        RecipeStep.objects.create(recipe=cake, order=1, description="Mix sugar and eggs.")
        RecipeStep.objects.create(recipe=cake, order=2, description="Add milk and stir.")
        RecipeStep.objects.create(recipe=cake, order=3, description="Bake at 180°C for 25 minutes.")

        update_recipe_nutrition(cake)

        # TODO: Fix this seed