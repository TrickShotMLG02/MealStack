# 🍲 Meal Stack

![License: GPL v3](https://img.shields.io/badge/license-GPL--3.0-blue)
![Meal Stack stable](https://img.shields.io/docker/v/trickshotmlg/mealstack/latest?label=stable&sort=semver)
![Meal Stack unstable](https://img.shields.io/docker/v/trickshotmlg/mealstack/dev?label=unstable&sort=semver)
![Python](https://img.shields.io/badge/python-3.12.4-blue)

## 📖 Description

Meal Stack is a Django recipe web application for managing, organizing, and sharing cooking recipes.
It supports recipe search, tagging, categories, localized UI text, recipe importers, and a refined recipe detail experience with cook mode, print export, and serving adjustments.

## 📌 Features

- Create, edit, and manage recipes
- Search recipes, ingredients, tags, and categories
- Browse recipes in a compact list layout and a polished detail view
- Adjust servings and recalculate displayed values
- Use cook mode for a compact, focused reading experience
- Export styled recipe PDFs for printing or saving
- Share recipe URLs, including the current serving selection
- Manage ingredients, units, tags, categories, and importers in the admin
- Import ingredients from OpenFoodFacts
- Import recipes from Chefkoch
- Use light and dark themes

## 📷 Preview

<p>
  <img src="docs/screenshots/recipe-list.png" alt="Meal Stack recipe list view" width="49%">
  <img src="docs/screenshots/recipe-detail.png" alt="Meal Stack recipe detail view" width="49%">
</p>

## 🚀 Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/TrickShotMLG02/MealStack.git
cd MealStack
cp .env.example .env
```

Adjust `.env` for your local setup. If you use Docker Compose, review `docker-compose.env` as well.

### 2. Install dependencies

Meal Stack uses `uv`:

```bash
uv python install
uv sync
```

### 3. Run migrations

```bash
uv run python manage.py migrate
```

### 4. Seed demo data

Run all seeds at once:

```bash
uv run python manage.py seed_all
```

Or run individual seeds:

```bash
uv run python manage.py seed_admin_user
uv run python manage.py seed_tags
uv run python manage.py seed_units
uv run python manage.py seed_ingredients
uv run python manage.py seed_recipe
```

### 5. Run the development server

```bash
uv run python manage.py runserver
```

Open:

- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

Default seed login:

- User: `admin`
- Password: `admin`

## 🐳 Docker Compose

The repository includes `docker-compose.yml` for local stack usage.

```bash
docker compose up --build
```

Compose uses:

- `.env` for application settings
- `docker-compose.env` for Compose-specific and stack-specific overrides

### 📦 Portainer

Portainer stacks cannot use `build:` for remote deployments. Build and push the image first, then replace the `build:` block with one of the published images:

- `trickshotmlg/mealstack:latest`
- `trickshotmlg/mealstack:dev`

For Portainer, comment out the active `env_file` block and provide stack variables through `stack.env`.

## 🐳 Docker Images

You can also run Meal Stack directly from Docker Hub:

```bash
docker run --env-file .env -p 8000:8000 trickshotmlg/mealstack:latest
```

Development image:

```bash
docker run --env-file .env -p 8000:8000 trickshotmlg/mealstack:dev
```

## 🤝 Contributing

Contributions are welcome.

- Check the [Contribution Issue](https://github.com/TrickShotMLG02/MealStack/issues/1) to get started.
- Fork the repo, make your changes, and submit a pull request.

## 🤖 AI Usage

This repository was founded and built by hand without AI tools.

AI was used selectively for:

- refactoring support
- idea generation
- complex implementation work such as fuzzy search
- web design and UI refinement
- debugging help
- README generation and rewording

AI-assisted changes were always reviewed, adapted where needed, and integrated deliberately. Nothing was copied blindly into the codebase.

## 📄 License

This project is licensed under the [GNU General Public License v3 (GPL-3.0)](LICENSE).
You are free to use, modify, and distribute this software under the terms of the GPL-3.0, which requires that any distributed modifications or derivative works also be open source.

Please give credit to the original authors when using or modifying this project.
