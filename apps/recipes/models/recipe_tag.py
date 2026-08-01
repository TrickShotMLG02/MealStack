from django.db import models
from django.utils.translation import gettext_lazy as _

class RecipeTag(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, verbose_name=_("Recipe"))
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, verbose_name=_("Tag"))

    class Meta:
        unique_together = ('recipe', 'tag')
        verbose_name = _("Recipe Tag")
        verbose_name_plural = _("Recipe Tags")

    def __str__(self):
        return f"{self.recipe} - {self.tag}"