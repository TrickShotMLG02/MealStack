import os
import uuid

from django.db import models
from django.utils.timezone import now


def recipe_image_upload_to(instance, filename):
    """
    Generates a unique filename for recipe images.
    Keeps year/month folders and adds a UUID for uniqueness.
    """
    ext = filename.split('.')[-1]  # preserve extension
    # timestamp-based folder
    year = now().year
    month = now().month
    # generate unique filename
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("recipes", str(year), str(month), filename)

class RecipeImage(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        #upload_to="recipes/%Y/%m/",
        upload_to=recipe_image_upload_to,
    )

    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)