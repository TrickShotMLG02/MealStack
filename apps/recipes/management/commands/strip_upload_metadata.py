from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import UnidentifiedImageError

from apps.recipes.models import RecipeImage
from apps.recipes.services.image_metadata import strip_image_metadata


class Command(BaseCommand):
    help = "Strip metadata from existing uploaded recipe images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report affected files without rewriting them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        checked = 0
        stripped_count = 0
        unchanged = 0
        missing = 0
        skipped = 0

        for recipe_image in RecipeImage.objects.exclude(image="").iterator():
            checked += 1
            image_field = recipe_image.image
            storage = image_field.storage
            name = image_field.name

            if not storage.exists(name):
                missing += 1
                self.stderr.write(f"Missing file: {name}")
                continue

            try:
                with storage.open(name, "rb") as image_file:
                    result = strip_image_metadata(image_file, name)
            except UnidentifiedImageError:
                skipped += 1
                self.stderr.write(f"Skipped unsupported image: {name}")
                continue

            if not result.had_metadata:
                unchanged += 1
                continue

            stripped_count += 1
            if dry_run:
                self.stdout.write(f"Would strip metadata: {name}")
                continue

            result.content.seek(0)
            try:
                storage_path = storage.path(name)
            except NotImplementedError:
                storage.delete(name)
                storage.save(name, ContentFile(result.content.read()))
            else:
                with open(storage_path, "wb") as target:
                    target.write(result.content.read())

            self.stdout.write(f"Stripped metadata: {name}")

        summary = (
            f"Checked {checked} image(s): {stripped_count} stripped, "
            f"{unchanged} unchanged, {missing} missing, {skipped} skipped."
        )
        if dry_run:
            summary = f"Dry run complete. {summary}"

        self.stdout.write(self.style.SUCCESS(summary))
