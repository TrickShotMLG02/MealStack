from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.text_formatting import slugify


class Ingredient(models.Model):
    ean = models.CharField(max_length=13, unique=True, null=True, blank=True, verbose_name=_("EAN"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    generic_name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Generic name"))
    brand = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Brand"))
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name=_("Slug"))

    # nutrition
    kcal = models.FloatField(default=0, verbose_name=_("kcal"))
    fat = models.FloatField(default=0, verbose_name=_("Fat"))
    saturates = models.FloatField(default=0, verbose_name=_("Saturates"))
    carbs = models.FloatField(default=0, verbose_name=_("Carbs"))
    sugar = models.FloatField(default=0, verbose_name=_("Sugar"))
    protein = models.FloatField(default=0, verbose_name=_("Protein"))
    salt = models.FloatField(default=0, verbose_name=_("Salt"))

    # grams per ml
    density = models.FloatField(null=True, blank=True, verbose_name=_("Density"))

    # metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Ingredient")
        verbose_name_plural = _("Ingredients")

    def save(self, *args, **kwargs):
        if not self.slug:
            ean_part = f"{self.ean}-" if self.ean else ""
            brand_part = f"{self.brand}-" if self.brand else ""
            self.slug = slugify(f"{ean_part}" if self.ean else f"{brand_part}{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
