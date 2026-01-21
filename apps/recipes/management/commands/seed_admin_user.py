from django.contrib.auth import get_user_model
from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial admin user"

    def get_seed_name(self):
        return "Admin User"


    def seed(self, *args, **kwargs):
        User = get_user_model()
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin"
        )
