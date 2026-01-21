from apps.recipes.models import Ingredient
from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial units"

    def get_seed_name(self):
        return "Units"


    def seed(self, *args, **kwargs):
        sugar, _ = Ingredient.objects.create(
            name="Sugar", kcal=400, protein=0, fat=0, carbs=100, salt=0
        )
        milk, _ = Ingredient.objects.create(
            name="Milk", kcal=60, protein=3, fat=3, carbs=5, salt=0, density=1.03
        )
        egg, _ = Ingredient.objects.create(
            name="Egg", kcal=155, protein=13, fat=11, carbs=1, salt=0.1
        )