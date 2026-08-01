from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.text_formatting import slugify


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Cuisine")
        verbose_name_plural = _("Cuisines")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name