# 🍲 Meal Stack

![License: GPL v3](https://img.shields.io/badge/license-GPL--3.0-blue)
![Meal Stack stable](https://img.shields.io/docker/v/trickshotmlg/mealstack?label=stable&sort=semver)
![Meal Stack unstable](https://img.shields.io/docker/v/trickshotmlg/mealstack/dev?label=unstable&sort=semver)
![Python](https://img.shields.io/badge/python-3.12.4-blue)


## 📖 Description

Meal Stack is a Django web application for **managing, organizing, and sharing cooking recipes**.  
It provides a structured way to store recipes, categorize them by cuisines and tags, and allows users to search, filter, and access recipes efficiently.

---

## 📌 Features

- Create, edit, and manage recipes
- Tag recipes with ingredients and units
- Admin interface for managing users, ingredients, recipes, and tags
- Support for importing recipes from other websites
- Seeded example data to get started quickly

---

## 🚀 Quick Start

Follow these steps to get Meal Stack running locally:

### 1️⃣ Clone & Setup
```
git clone https://github.com/TrickShotMLG02/MealStack.git
cd MealStack
cp .env.example .env
```
Edit .env to your configuration

### 2️⃣ Install Dependencies

Meal Stack supports **uv** as the package manager. If you don’t have uv installed, follow the installation guide: https://docs.astral.sh/uv/getting-started/
```
uv python install
uv sync
```

### 3️⃣ Database Setup

Create migrations
```
python manage.py makemigrations
```

Apply migrations
```
python manage.py migrate
```

### 4️⃣ Seed Initial Data

Choose either:

**Option 1: Run all seeds at once**
```
python manage.py seed_all
```

**Option 2: Run individual seeds**
```
python manage.py seed_admin_user
python manage.py seed_tags
python manage.py seed_units
python manage.py seed_ingredients
python manage.py seed_recipe
```

### 5️⃣ Collect Static Files
```
python manage.py collectstatic
```

### 6️⃣ Run the Development Server
```
python manage.py runserver
```

- Open your browser: http://127.0.0.1:8000/admin/
- Default login:
  - User: admin
  - Password: admin

---

## 🐳 Docker Images

You can also run Meal Stack using Docker. Pull the latest images from Docker Hub.


### Run latest stable image
```
docker run --env-file .env -p 8000:8000 trickshotmlg/mealstack:latest
```

### Run development image
```
docker run --env-file .env -p 8000:8000 trickshotmlg/mealstack:dev
```

---

## 🤝 Contributing

Contributions are welcome!  
- Check the [Contribution Issue](https://github.com/TrickShotMLG02/MealStack/issues/1) to get started.
- Fork the repo, make your changes, and submit a pull request.

---

## 📄 License

This project is licensed under the [GNU General Public License v3 (GPL-3.0)](LICENSE).  
You are free to use, modify, and distribute this software under the terms of the GPL-3.0, which requires that any distributed modifications or derivative works also be open source.  

Please give credit to the original authors when using or modifying this project.