from django.contrib import admin
from django.urls import path

from apps.recipes.views import admin_importers_view


class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request, context=None):
        app_list = super().get_app_list(request, context)

        importers_section = {
            "name": "Importers",
            "app_label": "importers",
            "url_path": "/admin/importers/",
            "models": [
                {
                    "name": importer["name"],
                    "object_name": importer["name"].lower().replace(" ", "_"),
                    "admin_url": f"/admin/importers/{importer['url_path']}",
                    "view_only": True,
                }
                for importer in admin_importers_view.IMPORTERS
            ],
        }
        app_list.append(importers_section)
        return app_list

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path("importers/", self.admin_view(admin_importers_view.importers_home), name="importers_home"),
        ]

        custom_importer_urls = [
            path(f"importers/{importer['url_path']}", self.admin_view(importer["view"]),
                 name=importer["name"].lower().replace(" ", "_"))
            for importer in admin_importers_view.IMPORTERS
        ]

        return custom_importer_urls + urls + custom_urls

my_admin_site = MyAdminSite(name="myadmin")

# TODO: Just a quick fix, consider registering stuff directly to this page
my_admin_site._registry = admin.site._registry.copy()