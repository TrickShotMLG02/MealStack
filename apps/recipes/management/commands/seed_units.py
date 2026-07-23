from apps.recipes.management.commands.SeedCommand import SeedCommand
from apps.recipes.management.commands.seed_catalog import UNIT_CATALOG, unit_defaults
from apps.recipes.models import Unit


class Command(SeedCommand):
    help = "Seed base units"

    def get_seed_name(self):
        return "Units"

    def seed(self, *args, **kwargs):
        for unit_data in UNIT_CATALOG:
            defaults = unit_defaults(unit_data["name"])
            Unit.objects.update_or_create(name=unit_data["name"], defaults=defaults)
