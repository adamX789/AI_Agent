from chat.models import *
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path="chat/management/commands/data.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        foods = data.get("foods")
        recipes = data.get("recipes")
        situations = data.get("situations")
        diets = data.get("diets")
        communication_styles = data.get("communication_styles")
        if foods:
            for item in foods:
                
            
