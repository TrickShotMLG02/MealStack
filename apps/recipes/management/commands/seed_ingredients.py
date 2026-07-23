from apps.common.text_formatting import slugify
from apps.recipes.management.commands.SeedCommand import SeedCommand
from apps.recipes.management.commands.seed_catalog import INGREDIENT_CATALOG, ingredient_defaults
from apps.recipes.models import Ingredient


class Command(SeedCommand):
    help = "Seed base ingredients"

    def get_seed_name(self):
        return "Ingredients"

    def seed(self, *args, **kwargs):
        for name, defaults in INGREDIENT_CATALOG.items():
            Ingredient.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    **ingredient_defaults(name),
                },
            )
