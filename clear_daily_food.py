import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

from user_profile.models import Food

def reset_daily_food():
    Food.objects.all().delete()
    print("denni data vynulovana")


if __name__ == "__main__":
    reset_daily_food()
