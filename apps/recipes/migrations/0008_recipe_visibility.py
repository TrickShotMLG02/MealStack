from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0007_recipecomponent"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="visibility",
            field=models.CharField(
                choices=[("listed", "Listed"), ("component_only", "Component only")],
                default="listed",
                help_text="Component-only recipes are available through linked recipes but are not shown independently to users.",
                max_length=20,
                verbose_name="Visibility",
            ),
        ),
    ]
