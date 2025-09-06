import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

from chat.models import Message
from user_profile.models import Food,Profile
from django.contrib.auth import get_user_model
from muj_den.funkce import sestav_jidelnicek

def reset_daily_food():
    Food.objects.all().delete()
    Message.objects.all().delete()
    User = get_user_model()
    users = User.objects.all()
    message_text = "Ahoj, na co máš dneska chuť, nebo co ti zbylo v lednici?😋 Zkusím ti podle toho sestavit jídelníček na základě tvých makroživin. Pokud nic nenapíšeš, vymyslím něco podle sebe."
    for user in users:
        profile = Profile.objects.get(user=user)
        sestav_jidelnicek(profile=profile,reset=True)
        Message.objects.create(
            user=user,
            text=message_text,
            sender="Podpora",
            role="agent"
        )
    print("denni data vynulovana a zprava vytvorena")


if __name__ == "__main__":
    reset_daily_food()
