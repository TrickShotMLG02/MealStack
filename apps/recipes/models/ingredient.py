from django.db import models
from django.utils.text import slugify


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    # nutrition
    kcal = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    salt = models.FloatField(default=0)

    density = models.FloatField(null=True, blank=True)

    # metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand}-{self.name}" if self.brand else self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name