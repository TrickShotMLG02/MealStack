from django.db import models
from django.utils.text import slugify
from apps.recipes.models.recipe_nutrition import RecipeNutrition

STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('published', 'Published'),
]

class Recipe(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    servings = models.PositiveIntegerField(default=1)
    source = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes'
    )

    tags = models.ManyToManyField(
        'Tag',
        through='RecipeTag',
        related_name='recipes',
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
