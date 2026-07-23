from django.core.management.base import BaseCommand, CommandError

from apps.recipes.importers.recipes.registry import get_recipe_importers


class Command(BaseCommand):
    help = "Import a single recipe using a selected or auto-detected recipe importer."

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            nargs="?",
            help="Recipe URL to import",
        )
        parser.add_argument(
            "-u",
            "--url",
            dest="url_option",
            help="Recipe URL to import",
        )
        parser.add_argument(
            "-i",
            "--importer",
            "--scraper",
            dest="importer_name",
            help="Recipe importer backend to use. Defaults to auto-detection by URL.",
        )

    def _get_importer_by_name(self, importer_name: str):
        for importer_spec in get_recipe_importers():
            if importer_spec.name.casefold() == importer_name.casefold():
                return importer_spec
        return None

    def _detect_importer(self, url: str):
        matches = [importer for importer in get_recipe_importers() if importer.matches_url(url)]
        if not matches:
            raise CommandError(
                "No registered recipe importer matches this URL. "
                "Pass --importer to select one explicitly."
            )
        if len(matches) > 1:
            match_names = ", ".join(importer.name for importer in matches)
            raise CommandError(
                "Multiple recipe importers match this URL: "
                f"{match_names}. Pass --importer to select one explicitly."
            )
        return matches[0]

    def handle(self, *args, **options):
        url = options.get("url_option") or options.get("url")
        if not url:
            raise CommandError("Please provide a recipe URL via positional argument or --url.")

        importer_name = (options.get("importer_name") or "").strip()
        if importer_name:
            importer_spec = self._get_importer_by_name(importer_name)
            if importer_spec is None:
                available = ", ".join(importer.name for importer in get_recipe_importers())
                raise CommandError(
                    f"Importer '{importer_name}' is not registered. "
                    f"Available importers: {available}."
                )
            if not importer_spec.matches_url(url):
                raise CommandError(
                    f"URL does not match the selected importer '{importer_spec.name}'."
                )
        else:
            importer_spec = self._detect_importer(url)

        importer = importer_spec.importer_cls(url=url)

        recipe = importer.import_recipe()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported recipe '{recipe.title}' via {importer_spec.name}."
            )
        )
