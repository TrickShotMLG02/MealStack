import os
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Determine environment
ENV = os.getenv("MEALSTACK_ENV", "dev")  # default to dev

if ENV == "dev":
    SETTINGS_MODULE = "MealStack.settings.dev"
elif ENV == "prod":
    SETTINGS_MODULE = "MealStack.settings.prod"
else:
    raise ValueError(f"Unknown MEALSTACK_ENV: {ENV}")

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE)