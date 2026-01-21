from django.core.management import call_command, BaseCommand
from apps.recipes.management.commands.seed_admin_user import Command as SeedAdminUser
from apps.recipes.management.commands.seed_units import Command as SeedUnits

class Command(BaseCommand):
    help = "Run all seed commands"

    def get_seed_name(self):
        return "Full Seed"

    SEED_COMMANDS = [
        SeedAdminUser,
        SeedUnits,
    ]

    def handle(self, *args, **kwargs):
        total = len(self.SEED_COMMANDS)
        success_count = 0
        failed = []

        self.stdout.write(f"Starting full seeding process for {total} Seeds...")
        self.stdout.write("-" * 40)

        for seed_cls in self.SEED_COMMANDS:
            try:
                seed_command = seed_cls()
                seed_name = seed_cls.__module__.split('.')[-1]
                seed_command.handle(silent=True, raise_on_error=True)
                self.stdout.write(self.style.SUCCESS(f"✅ {seed_name} succeeded"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {seed_name} failed: {e}"))
                failed.append(seed_name)

        self.stdout.write("-" * 40)
        self.stdout.write(self.style.SUCCESS(f"✅ {success_count}/{total} seeds succeeded"))
        if failed:
            self.stdout.write(self.style.WARNING(f"⚠ {len(failed)}/{total} seeds failed: {', '.join(failed)}"))
