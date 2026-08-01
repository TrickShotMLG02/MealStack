from django.db import models
from django.utils.translation import gettext_lazy as _

class RecipeNote(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        verbose_name=_("Recipe"),
    )

    content = models.TextField(blank=True, null=True, verbose_name=_("Content"))

    ordering = models.PositiveIntegerField(default=0, verbose_name=_("Ordering"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        ordering = ["ordering", "id"]
        verbose_name = _("Recipe Note")
        verbose_name_plural = _("Recipe Notes")
        indexes = [
            models.Index(fields=["recipe"]),
        ]

    def __str__(self):
        return f"Note for {self.recipe}"
