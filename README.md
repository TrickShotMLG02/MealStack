## Meal Stack


### Initial Setup
- Copy `.env.example` to `.env` and edit settings
- Create admin user: `python manage.py createsuperuser`
- Make Migrations: `python manage.py makemigrations`
- Migrate: `python manage.py migrate`
- Set-Up Initial test data: `python manage.py seed_test_data`
- Run Server: `python manage.py runserver`
- Access http://127.0.0.1:8000/admin/