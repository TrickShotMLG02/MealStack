from django.db import models
from django.utils.translation import gettext_lazy as _

class RecipeStepGroup(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, verbose_name=_("Recipe"))
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Name"))

    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        ordering = ['order']
        verbose_name = _("Recipe Step Group")
        verbose_name_plural = _("Recipe Step Groups")

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "Main"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name