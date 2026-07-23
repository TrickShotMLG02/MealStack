from apps.recipes.importers.ingredients.openfoodfacts import OpenFoodFactsImporter

def main():
    importer = OpenFoodFactsImporter()
    importer.import_ingredient("1103086260005")


if __name__ == '__main__':
    main()