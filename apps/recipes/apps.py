from django.apps import AppConfig


class RecipesConfig(AppConfig):
    name = "apps.recipes"

    def ready(self):
        import apps.recipes.signals