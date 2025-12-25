

#if __name__ == '__main__':
    #from recipe_scrapers import SCRAPERS

    # supported websites
    #print(SCRAPERS.keys())

    #from recipe_scrapers import scrape_me

    #scraper = scrape_me("https://www.chefkoch.de/rezepte/3520631525089100/Tomaten-Kaesesauce-mit-Fleischwurst.html")
    #print(scraper.title())
    #print(scraper.instructions())
    #print(scraper.to_json())
    # for a complete list of methods:
    #help(scraper)

import os
import django

# 1️⃣ Set the settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MealStack.settings.dev")  # or prod

# 2️⃣ Initialize Django
django.setup()

# 3️⃣ Now you can import models and importers safely
from apps.recipes.importers.chefkoch import ChefkochImporter

def main():
    url = "https://www.chefkoch.de/rezepte/3520631525089100/Tomaten-Kaesesauce-mit-Fleischwurst.html?portionen=4"

    importer = ChefkochImporter(url)

    print(importer.to_json(indent=2))

    recipe = importer.import_recipe()
    print(recipe.title)
    for ri in recipe.recipeingredient_set.all():
        print(f"{ri.quantity} {ri.unit.name} {ri.ingredient.name}")

if __name__ == "__main__":
    main()