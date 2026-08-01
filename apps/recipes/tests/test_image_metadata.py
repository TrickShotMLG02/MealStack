from io import BytesIO
from pathlib import Path
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from apps.recipes.models import Recipe, RecipeImage


def jpeg_with_exif() -> bytes:
    image = Image.new("RGB", (12, 12), color="red")
    exif = Image.Exif()
    exif[0x010E] = "private description"

    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


class RecipeImageMetadataTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_recipe_image_upload_strips_exif_metadata(self):
        recipe = Recipe.objects.create(title="Cake")
        upload = SimpleUploadedFile(
            "cake.jpg",
            jpeg_with_exif(),
            content_type="image/jpeg",
        )

        recipe_image = RecipeImage.objects.create(recipe=recipe, image=upload)

        with Image.open(recipe_image.image.path) as saved_image:
            self.assertFalse(saved_image.getexif())

    def test_strip_upload_metadata_command_strips_existing_files(self):
        recipe = Recipe.objects.create(title="Cake")
        image_name = "recipes/2026/8/cake.jpg"
        image_path = Path(self.media_root) / image_name
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(jpeg_with_exif())
        RecipeImage.objects.create(recipe=recipe, image=image_name)

        call_command("strip_upload_metadata", verbosity=0)

        with Image.open(image_path) as saved_image:
            self.assertFalse(saved_image.getexif())
