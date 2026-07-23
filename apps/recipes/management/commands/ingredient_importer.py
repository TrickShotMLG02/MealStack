from django.core.management.base import BaseCommand, CommandError

from apps.recipes.importers.ingredients.base import EANNotFound
from apps.recipes.importers.ingredients.openfoodfacts import OpenFoodFactsImporter


class Command(BaseCommand):
    help = "Import a single ingredient by EAN using a selected importer."

    SUPPORTED_IMPORTERS = {
        "openfoodfacts": OpenFoodFactsImporter,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "ean",
            nargs="?",
            help="EAN code to import",
        )
        parser.add_argument(
            "-e",
            "--ean",
            dest="ean_option",
            help="EAN code to import",
        )
        parser.add_argument(
            "-i",
            "--importer",
            "--scraper",
            dest="importer_name",
            default="openfoodfacts",
            help="Importer backend to use (default: openfoodfacts)",
        )

    def handle(self, *args, **options):
        ean = options.get("ean_option") or options.get("ean")
        if not ean:
            raise CommandError("Please provide an EAN via positional argument or --ean.")

        importer_name = (options.get("importer_name") or "openfoodfacts").strip().lower()
        importer_cls = self.SUPPORTED_IMPORTERS.get(importer_name)
        if importer_cls is None:
            raise CommandError(
                f"Importer '{importer_name}' is not implemented yet. "
                f"Supported importers: {', '.join(sorted(self.SUPPORTED_IMPORTERS))}."
            )

        importer = importer_cls(ean=ean)

        try:
            ingredient = importer.import_ingredient()
        except EANNotFound as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported ingredient '{ingredient.name}' from OpenFoodFacts ({ingredient.ean})."
            )
        )
