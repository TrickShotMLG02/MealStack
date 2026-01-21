from apps.recipes.models import Unit
from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial units"

    def get_seed_name(self):
        return "Units"


    def seed(self, *args, **kwargs):
        gram, _ = Unit.objects.get_or_create(name="gram", type="weight", grams_per_unit=1)
        ml, _ = Unit.objects.get_or_create(name="ml", type="volume", ml_per_unit=1)
        piece, _ = Unit.objects.get_or_create(name="piece", type="count")