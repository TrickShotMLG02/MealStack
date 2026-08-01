from django.db import models
from django.utils.translation import gettext_lazy as _

class RecipeStep(models.Model):
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    description = models.TextField(verbose_name=_("Description"))

    group = models.ForeignKey('RecipeStepGroup', on_delete=models.CASCADE, verbose_name=_("Group"))

    class Meta:
        ordering = ['order']
        verbose_name = _("Recipe Step")
        verbose_name_plural = _("Recipe Steps")

    def __str__(self):
        group_name = f" ({self.group.name})" if self.group else ""
        return f"Step {self.order} {group_name}"
