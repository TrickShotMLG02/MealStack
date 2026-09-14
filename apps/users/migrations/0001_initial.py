from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("recipes", "0006_alter_cuisine_options_alter_ingredient_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeBookmark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookmarks", to="recipes.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipe_bookmarks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Recipe bookmark",
                "verbose_name_plural": "Recipe bookmarks",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RecipeList",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Name")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recipes", models.ManyToManyField(blank=True, related_name="user_lists", to="recipes.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipe_lists", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Recipe list",
                "verbose_name_plural": "Recipe lists",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="recipebookmark",
            constraint=models.UniqueConstraint(fields=("user", "recipe"), name="unique_user_recipe_bookmark"),
        ),
        migrations.AddConstraint(
            model_name="recipelist",
            constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_user_recipe_list_name"),
        ),
    ]
