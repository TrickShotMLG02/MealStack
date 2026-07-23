from django.core.management import BaseCommand

from apps.recipes.management.commands.seed_admin_user import Command as SeedAdminUser
from apps.recipes.management.commands.seed_ingredients import Command as SeedIngredients
from apps.recipes.management.commands.seed_recipe import Command as SeedRecipe
from apps.recipes.management.commands.seed_tags import Command as SeedTags
from apps.recipes.management.commands.seed_units import Command as SeedUnits


class Command(BaseCommand):
    help = "Run all seed commands"

    SEED_COMMANDS = [
        SeedAdminUser,
        SeedUnits,
        SeedTags,
        SeedIngredients,
        SeedRecipe,
    ]

    def handle(self, *args, **kwargs):
        total = len(self.SEED_COMMANDS)
        success_count = 0
        failed = []

        self.stdout.write(f"Starting full seeding process for {total} seeds...")
        self.stdout.write("-" * 40)

        for seed_cls in self.SEED_COMMANDS:
            seed_command = seed_cls()
            seed_name = seed_cls.__module__.split(".")[-1]
            try:
                seed_command.handle(silent=True, raise_on_error=True)
                self.stdout.write(self.style.SUCCESS(f"OK {seed_name} succeeded"))
                success_count += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"FAIL {seed_name} failed: {exc}"))
                failed.append(seed_name)

        self.stdout.write("-" * 40)
        self.stdout.write(self.style.SUCCESS(f"OK {success_count}/{total} seeds succeeded"))
        if failed:
            self.stdout.write(self.style.WARNING(f"WARN {len(failed)}/{total} seeds failed: {', '.join(failed)}"))
