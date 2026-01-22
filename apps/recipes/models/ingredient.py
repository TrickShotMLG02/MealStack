from django.db import models
from apps.common.text_formatting import slugify


class Ingredient(models.Model):
    ean = models.CharField(max_length=13, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    # nutrition
    kcal = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    salt = models.FloatField(default=0)

    # grams per ml
    density = models.FloatField(null=True, blank=True)

    # metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            ean_part = f"{self.ean}-" if self.ean else ""
            brand_part = f"{self.brand}-" if self.brand else ""
            self.slug = slugify(f"{ean_part}" if self.ean else f"{brand_part}{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name