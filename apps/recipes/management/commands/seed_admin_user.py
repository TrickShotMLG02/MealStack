from django.contrib.auth import get_user_model

from apps.recipes.management.commands.SeedCommand import SeedCommand


class Command(SeedCommand):
    help = "Seed initial admin user"

    def get_seed_name(self):
        return "Admin User"

    def seed(self, *args, **kwargs):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )
        user.email = "admin@example.com"
        user.is_staff = True
        user.is_superuser = True
        user.set_password("admin")
        user.save()
