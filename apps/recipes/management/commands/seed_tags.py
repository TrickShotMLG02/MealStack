from apps.recipes.management.commands.SeedCommand import SeedCommand
from apps.recipes.management.commands.seed_catalog import TAG_CATALOG
from apps.recipes.models import Tag
from apps.common.text_formatting import slugify


class Command(SeedCommand):
    help = "Seed base tags"

    def get_seed_name(self):
        return "Tags"

    def seed(self, *args, **kwargs):
        for name in TAG_CATALOG:
            Tag.objects.update_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )
