from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0006_alter_cuisine_options_alter_ingredient_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeComponent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "servings",
                    models.FloatField(
                        help_text="How many servings of the linked recipe are used in the parent recipe.",
                        validators=[django.core.validators.MinValueValidator(0.000001)],
                        verbose_name="Used servings",
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Order")),
                (
                    "title_override",
                    models.CharField(
                        blank=True,
                        help_text="Optional heading shown for this linked recipe.",
                        max_length=250,
                        verbose_name="Section title override",
                    ),
                ),
                (
                    "child_recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="used_in_recipes",
                        to="recipes.recipe",
                        verbose_name="Linked recipe",
                    ),
                ),
                (
                    "parent_recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="components",
                        to="recipes.recipe",
                        verbose_name="Parent recipe",
                    ),
                ),
            ],
            options={
                "verbose_name": "Recipe Component",
                "verbose_name_plural": "Recipe Components",
                "ordering": ["order", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="recipecomponent",
            constraint=models.UniqueConstraint(
                fields=("parent_recipe", "child_recipe"),
                name="unique_recipe_component",
            ),
        ),
        migrations.AddConstraint(
            model_name="recipecomponent",
            constraint=models.CheckConstraint(
                condition=~models.Q(parent_recipe=models.F("child_recipe")),
                name="recipe_component_not_self_linked",
            ),
        ),
        migrations.AddConstraint(
            model_name="recipecomponent",
            constraint=models.CheckConstraint(
                condition=models.Q(servings__gt=0),
                name="recipe_component_servings_positive",
            ),
        ),
        migrations.AddIndex(
            model_name="recipecomponent",
            index=models.Index(fields=["parent_recipe", "order"], name="recipe_comp_parent_order_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomponent",
            index=models.Index(fields=["child_recipe"], name="recipe_comp_child_idx"),
        ),
    ]
