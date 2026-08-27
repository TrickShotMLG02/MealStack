from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

from apps.recipes.views import admin_importers_view


class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request, context=None):
        app_list = super().get_app_list(request, context)

        ingredient_importers_section = {
            "name": _("Ingredient Importers"),
            "app_label": "ingredient_importers",
            "url_path": "/admin/importers/ingredient/",
            "models": [
                {
                    "name": importer["name"],
                    "object_name": importer["name"].lower().replace(" ", "_"),
                    "admin_url": f"/admin/importers/{importer['url_path']}",
                    "view_only": True,
                }
                for importer in admin_importers_view.INGREDIENT_IMPORTERS
            ],
        }
        recipe_importers_section = {
            "name": _("Recipe Scrapers"),
            "app_label": "recipe_scrapers",
            "url_path": "/admin/importers/recipe/",
            "models": [
                {
                    "name": importer["name"],
                    "object_name": importer["name"].lower().replace(" ", "_"),
                    "admin_url": f"/admin/importers/{importer['url_path']}",
                    "view_only": True,
                }
                for importer in admin_importers_view.get_recipe_importer_entries()
            ],
        }
        app_list.extend([ingredient_importers_section, recipe_importers_section])
        return app_list

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path("importers/", self.admin_view(admin_importers_view.importers_home), name="importers_home"),
            path("importers/ingredient/", self.admin_view(admin_importers_view.ingredient_importers_home), name="ingredient_importers_home"),
            path("importers/recipe/", self.admin_view(admin_importers_view.recipe_importers_home), name="recipe_importers_home"),
        ]

        custom_importer_urls = [
            path(f"importers/{importer['url_path']}", self.admin_view(importer["view"]),
                 name=importer["name"].lower().replace(" ", "_"))
            for importer in (
                admin_importers_view.INGREDIENT_IMPORTERS + admin_importers_view.get_recipe_importer_entries()
            )
        ]

        return custom_importer_urls + custom_urls + urls

my_admin_site = MyAdminSite(name="myadmin")

# TODO: Just a quick fix, consider registering stuff directly to this page
my_admin_site._registry = admin.site._registry.copy()

# The users admin module may be autodiscovered after this registry snapshot.
# Register its models explicitly on the site that is mounted by the project.
from apps.users.admin import OIDCIdentityAdmin, OIDCProviderAdmin
from apps.users.models import OIDCIdentity, OIDCProvider

my_admin_site.register(OIDCProvider, OIDCProviderAdmin)
my_admin_site.register(OIDCIdentity, OIDCIdentityAdmin)
