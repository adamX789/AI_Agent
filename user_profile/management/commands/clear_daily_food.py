from django.core.management.base import BaseCommand
from user_profile.models import Food

class Command(BaseCommand):
    def handle(self, *args, **options):
        Food.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Smazání objektů proběhlo úspěšně!'))