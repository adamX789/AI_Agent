from chat.models import *
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from google import genai
from google.genai import types


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        file_path = "chat/data.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        foods = data.get("foods")
        recipes = data.get("recipes")
        situations = data.get("situations")
        diets = data.get("diets")
        communication_styles = data.get("communication_styles")
        with transaction.atomic():
            self.import_potraviny(foods, client)
            self.import_recepty(recipes, client)
            self.import_situace(situations, client)
            self.import_diety(diets,client)
            self.import_komunikace(communication_styles,client)

    def import_potraviny(self, foods, client):
        if not foods:
            return None
        for item in foods:
            embedding_text = f"""
            Název: {item["name"]}
            Popis: {item["description"]}
            Výhody: {", ".join(item["benefits"])}
            Nejlepší pro: {", ".join(item["best_for"])}
            Nekonzumujte pokud: {", ".join(item["avoid_if"])}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            potravina, created = Potraviny.objects.get_or_create(
                nazev=item["name"],
                popis=item["description"],
                vyhody=item["benefits"],
                nejlepsi_pro=item["best_for"],
                nekonzumujte_pokud=item["avoid_if"],
                embedding=embedding
            )
            if created:
                Makroziviny.objects.create(
                    potravina=potravina,
                    bilkoviny_gramy=item["nutrients"]["protein_g"],
                    sacharidy_gramy=item["nutrients"]["carbs_g"],
                    tuky_gramy=item["nutrients"]["fat_g"]
                )

    def import_recepty(self, recipes, client):
        if not recipes:
            return None
        for item in recipes:
            embedding_text = f"""
            Název: {item["name"]}
            Ingredience: {", ".join(item["ingredients"])}
            Instrukce: {item["instructions"]}
            Vhodné pro: {", ".join(item["suitable_for"])}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            Recepty.objects.get_or_create(
                nazev=item["name"],
                ingredience=item["ingredients"],
                instrukce=item["instructions"],
                vhodne_pro=item["suitable_for"],
                embedding=embedding
            )

    def import_situace(self, situations, client):
        if not situations:
            return None
        for item in situations:
            embedding_text = f"""
            Popis situace: {item["situation"]}
            Rada: {item["advice"]}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            Situace.objects.get_or_create(
                popis_situace=item["situation"],
                rada=item["advice"],
                embedding=embedding
            )
    def import_diety(self,diets,client):
        if not diets:
            return None
        
        for item in diets:
            embedding_text = f"""
            Název diety: {item["name"]}
            Popis: {item["description"]}
            Výhody: {", ".join(item["benefits"])}
            Není doporučeno pro: {", ".join(item["not_suitable_for"])}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            Diety.objects.get_or_create(
                nazev_diety=item["name"],
                popis=item["description"],
                vyhody=item["benefits"],
                neni_doporuceno_pro=item["not_suitable_for"],
                embedding=embedding
            )
    def import_komunikace(self,communication_styles,client):
        if not communication_styles:
            return None
        for item in communication_styles:
            embedding_text = f"""
            Styl komunikace: {item["style_id"]}
            Příklad: {item["example"]}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            StylyKomunikace.objects.get_or_create(
                styl=item["style_id"],
                priklad=item["example"],
                embedding=embedding
            )