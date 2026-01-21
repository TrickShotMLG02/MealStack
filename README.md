## Meal Stack


### Initial Setup
- Copy `.env.example` to `.env` and edit settings
- Make Migrations: `python manage.py makemigrations`
- Migrate: `python manage.py migrate`
- Seed initial data:
  - Option 1: Run all seeds at once
    - `python manage.py seed_all`
  - Option 2: Run individual seeds separately
    - `python manage.py seed_admin_user`
    - `python manage.py seed_tags`
    - `python manage.py seed_units`
    - `python manage.py seed_ingredients`
    - `python manage.py seed_recipe`
- Collect static files: `python manage.py collectstatic`
- Run Server: `python manage.py runserver`
- Access http://127.0.0.1:8000/admin/
- Login as user `admin` with password `admin`