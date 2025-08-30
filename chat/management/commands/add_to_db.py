from chat.models import *
import json
import os
from dotenv import load_dotenv
from django.db.models.expressions import RawSQL
from django.core.management.base import BaseCommand
from django.db import transaction
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def search_recepty(ingredience):
    kalorie = 0
    bilkoviny = 0
    sacharidy = 0
    tuky = 0
    for item in ingredience:
        potravina = item["nazev"]
        mnozstvi = item["mnozstvi"]
        casti = mnozstvi.strip().split(" ")
        hodnota = float(casti[0])
        jednotka = casti[1]
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=potravina,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        embedding = response.embeddings[0].values
        potravina_objekt = Potraviny.objects.annotate(podoba=RawSQL(
            "%s::vector <=> embedding", (embedding,))).order_by("podoba").first()
        if potravina_objekt.podoba < 0.35:
            makroziviny = potravina_objekt.makroziviny
            koeficient = hodnota/100
            kalorie += makroziviny.kalorie*koeficient
            bilkoviny += makroziviny.bilkoviny_gramy*koeficient
            sacharidy += makroziviny.sacharidy_gramy*koeficient
            tuky += makroziviny.tuky_gramy*koeficient
    return int(round(kalorie)), round(bilkoviny, 2), round(sacharidy, 2), round(tuky, 2)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = "chat/data.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        foods = data.get("foods")
        recipes = data.get("recipes")
        situations = data.get("situations")
        diets = data.get("diets")
        communication_styles = data.get("communication_styles")
        with transaction.atomic():
            self.import_potraviny(foods)
            self.import_recepty(recipes)
            self.import_situace(situations)
            self.import_diety(diets)
            self.import_komunikace(communication_styles)

    def import_potraviny(self, foods):
        print("pridavam potraviny")
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
                    kalorie=item["nutrients"]["kcal"],
                    bilkoviny_gramy=item["nutrients"]["protein_g"],
                    sacharidy_gramy=item["nutrients"]["carbs_g"],
                    tuky_gramy=item["nutrients"]["fat_g"]
                )

    def import_recepty(self, recipes):
        print("pridavam recepty")
        if not recipes:
            return None
        for item in recipes:
            embedding_text = f"""
            Název: {item["name"]}
            Ingredience: {", ".join(item["ingredients"])}
            Instrukce: {item["instructions"]}
            Typ jídla: {item["meal_type"]}
            Teplota: {item["temperature"]}
            Čas přípravy v minutách: {item["prep_time_min"]}
            Vhodné pro: {", ".join(item["suitable_for"])}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            recept, created = Recepty.objects.get_or_create(
                nazev=item["name"],
                ingredience=item["ingredients"],
                instrukce=item["instructions"],
                typ_jidla=item["meal_type"],
                teplota=item["temperature"],
                cas_pripravy_min=item["prep_time_min"],
                vhodne_pro=item["suitable_for"],
                embedding=embedding
            )
            if created:
                kalorie, bilkoviny, sacharidy, tuky = search_recepty(
                    ingredience=item["ingredients"])
                MakrozivinyRecepty.objects.create(
                    recept=recept,
                    kalorie=kalorie,
                    bilkoviny_gramy=bilkoviny,
                    sacharidy_gramy=sacharidy,
                    tuky_gramy=tuky
                )

    def import_situace(self, situations):
        print("pridavam situace")
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

    def import_diety(self, diets):
        print("pridavam diety")
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

    def import_komunikace(self, communication_styles):
        print("pridavam komunikace")
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
