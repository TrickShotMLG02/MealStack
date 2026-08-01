import os
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from apps.recipes.models.recipe_nutrition import RecipeNutrition
from apps.common.text_formatting import slugify
from apps.common.time import format_timedelta

STATUS_CHOICES = [
    ('draft', _('Draft')),
    ('published', _('Published')),
]

class Recipe(models.Model):
    class Meta:
        verbose_name = _("Recipe")
        verbose_name_plural = _("Recipes")

    title = models.CharField(max_length=250, verbose_name=_("Title"))
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name=_("Slug"))

    servings = models.PositiveIntegerField(default=1, verbose_name=_("Servings"))

    preparation_time = models.DurationField(null=True, blank=True, verbose_name=_("Preparation time"))
    cooking_time = models.DurationField(null=True, blank=True, verbose_name=_("Cooking time"))
    resting_time = models.DurationField(null=True, blank=True, verbose_name=_("Resting time"))

    cuisine = models.ForeignKey(
        'Cuisine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Cuisine"),
    )

    source = models.URLField(blank=True, null=True, verbose_name=_("Source"))
    author = models.CharField(max_length=40, blank=True, null=True, verbose_name=_("Author"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    """
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes'
    )
    """

    tags = models.ManyToManyField(
        'Tag',
        through='RecipeTag',
        related_name='recipes',
        blank=True
    )

    @property
    def total_time(self):
        return (
                (self.preparation_time or timedelta())
                + (self.cooking_time or timedelta())
                + (self.resting_time or timedelta())
        )


    def total_time_display(self):
        """
        Optional: format for admin display
        """
        total = self.total_time
        return format_timedelta(total)

    total_time_display.short_description = "Total Time"


    @property
    def primary_or_placeholder(self):
        """
        Returns the primary image if it exists on disk.
        Otherwise, returns the placeholder image.
        """
        primary = self.recipeimage_set.filter(is_primary=True).first()
        if primary and primary.image:
            image_path = os.path.join(settings.MEDIA_ROOT, primary.image.name)
            if os.path.exists(image_path):
                return primary.image.url
        return static('recipes/images/placeholder.jpg')

    @property
    def images_or_placeholder(self):
        """
        Returns a list of RecipeImage objects.
        If an image is missing or the file doesn't exist, its URL is replaced with a placeholder.
        If no images exist, returns a single placeholder.
        """
        class DummyImage:
            @property
            def image(self):
                class ImageAttr:
                    url = static('recipes/images/placeholder.jpg')

                return ImageAttr()

        images = list(self.recipeimage_set.all().order_by('-is_primary', 'ordering'))
        if not images:
            return [DummyImage()]

        result = []
        for img in images:
            # Check if ImageField exists and file is on disk
            path_exists = img.image and os.path.exists(os.path.join(settings.MEDIA_ROOT, img.image.name))
            result.append(img if path_exists else DummyImage())

        return result


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.preparation_time:
            self.preparation_time = timedelta(seconds=0)
        if not self.cooking_time:
            self.cooking_time = timedelta(seconds=0)
        if not self.resting_time:
            self.resting_time = timedelta(seconds=0)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
