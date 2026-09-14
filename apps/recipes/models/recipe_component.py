from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class RecipeComponent(models.Model):
    """A reusable recipe used as part of another recipe."""

    parent_recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name=_("Parent recipe"),
    )
    child_recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.PROTECT,
        related_name="used_in_recipes",
        verbose_name=_("Linked recipe"),
    )
    servings = models.FloatField(
        validators=[MinValueValidator(0.000001)],
        verbose_name=_("Used servings"),
        help_text=_("How many servings of the linked recipe are used in the parent recipe."),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    title_override = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_("Section title override"),
        help_text=_("Optional heading shown for this linked recipe."),
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Recipe Component")
        verbose_name_plural = _("Recipe Components")
        constraints = [
            models.UniqueConstraint(
                fields=["parent_recipe", "child_recipe"],
                name="unique_recipe_component",
            ),
            models.CheckConstraint(
                condition=~models.Q(parent_recipe=models.F("child_recipe")),
                name="recipe_component_not_self_linked",
            ),
            models.CheckConstraint(
                condition=models.Q(servings__gt=0),
                name="recipe_component_servings_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["parent_recipe", "order"], name="recipe_comp_parent_order_idx"),
            models.Index(fields=["child_recipe"], name="recipe_comp_child_idx"),
        ]

    def clean(self):
        super().clean()

        if not self.parent_recipe_id or not self.child_recipe_id:
            return

        if self.parent_recipe_id == self.child_recipe_id:
            raise ValidationError({"child_recipe": _("A recipe cannot link to itself.")})

        # Follow existing component edges from the proposed child. If the
        # proposed parent is reachable, saving this component would create a
        # cycle such as A -> B -> A.
        pending = [self.child_recipe_id]
        visited = set()
        while pending:
            recipe_id = pending.pop()
            if recipe_id in visited:
                continue
            visited.add(recipe_id)
            if recipe_id == self.parent_recipe_id:
                raise ValidationError({"child_recipe": _("Recipe components cannot contain a circular reference.")})
            pending.extend(
                RecipeComponent.objects.filter(parent_recipe_id=recipe_id)
                .exclude(pk=self.pk)
                .values_list("child_recipe_id", flat=True)
            )

    def __str__(self):
        return f"{self.parent_recipe} → {self.child_recipe}"
