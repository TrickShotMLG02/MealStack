from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecipesConfig(AppConfig):
    name = "apps.recipes"
    verbose_name = _("Recipes")

    def ready(self):
        import apps.recipes.signals