from apps.recipes.models import Tag
from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial units"

    def get_seed_name(self):
        return "Units"


    def seed(self, *args, **kwargs):
        dessert_tag, _ = Tag.objects.create(name="Dessert")
        breakfast_tag, _ = Tag.objects.create(name="Breakfast")