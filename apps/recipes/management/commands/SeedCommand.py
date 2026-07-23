from abc import ABC, abstractmethod

from django.core.management import BaseCommand


class SeedCommand(BaseCommand, ABC):
    help = "Abstract base seeder."

    @abstractmethod
    def get_seed_name(self):
        """
        This method is called for printing the seed name.
        """
        pass

    def handle(self, *args, silent=False, raise_on_error=False, **kwargs):
        """
        This method is called by Django when you run the command.
        It delegates the actual seeding to the `seed` method, which
        subclasses must implement.
        """

        def write(msg: str):
            if not silent:
                self.stdout.write(msg)

        write(f"Seeding {self.get_seed_name()}...")
        try:
            self.seed(*args, **kwargs)
        except Exception as exc:
            write(f"Failed to seed {self.get_seed_name()}: {exc}")
            if raise_on_error:
                raise exc
        else:
            write(self.style.SUCCESS(f"Successfully seeded {self.get_seed_name()}."))

    @abstractmethod
    def seed(self, *args, **kwargs):
        """
        Subclasses must implement this method to perform the actual seeding logic.
        """
        pass
