from chat.models import *
import json
import os
from dotenv import load_dotenv
from django.db.models.expressions import RawSQL
from django.core.management.base import BaseCommand
from django.db import transaction
from google import genai
from google.genai import types
from pydantic import BaseModel,Field
from decimal import Decimal

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class PrevodJednotekKusy(BaseModel):
    pocet_gramu_na_kus:float = Field(description="Kolik gramů má 1 kus dané potraviny.")

class PrevodJednotekPlatky(BaseModel):
    pocet_gramu_na_platek:float = Field(description="Kolik gramů má 1 plátek dané potraviny.")

def call_llm(potravina,jednotka):
    contents = types.Content(role="user",parts=[types.Part(text=f"Potravina: {potravina}")])
    if jednotka in ["ks","kus","kusy","kusu","kusů"]:
        config = types.GenerateContentConfig(system_instruction="Jsi expert na převod jednotek jídla. Tvým úkolem je zjistit, kolik gramů má 1 kus dané potraviny",response_schema=PrevodJednotekKusy,response_mime_type="application/json")
    elif jednotka in ["plátek","plátky","plátků"]:
        config = types.GenerateContentConfig(system_instruction="Jsi expert na převod jednotek jídla. Tvým úkolem je zjistit, kolik gramů má 1 plátek dané potraviny",response_schema=PrevodJednotekPlatky,response_mime_type="application/json")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )
    if jednotka in ["ks","kus","kusy","kusu","kusů"]:
        final_response_kusy:PrevodJednotekKusy = response.parsed
        return final_response_kusy.pocet_gramu_na_kus
    elif jednotka in ["plátek","plátky","plátků"]:
        final_response_platky:PrevodJednotekPlatky = response.parsed
        return final_response_platky.pocet_gramu_na_platek
    
def search_recepty(ingredience):
    kalorie = 0
    bilkoviny = 0
    sacharidy = 0
    tuky = 0
    for item in ingredience:
        potravina = item["nazev"]
        mnozstvi = item["mnozstvi"]
        if mnozstvi == "špetka" or potravina == "Sůl" or potravina == "Pepř":
            continue
        print(f"hledam potravinu: {potravina}")
        casti = mnozstvi.strip().split(" ")
        hodnota_str = casti[0]
        try:
            hodnota = float(hodnota_str)
        except ValueError:
            numerator, denominator = map(float, hodnota_str.split('/'))
            hodnota = numerator / denominator
        jednotka = casti[1].lower()
        kusy_platky_list = ["ks","kus","kusy","kusu","kusů","plátek","plátky","plátků"]
        kila_litry_list = ["kg","l"]
        if jednotka in kusy_platky_list:
            result = call_llm(potravina=potravina,jednotka=jednotka)
            koeficient = (hodnota*result)/100
        elif jednotka in kila_litry_list:
            koeficient = hodnota*10
        else:
            koeficient = hodnota/100

        potravina_objekt = Potraviny.objects.filter(nazev=potravina).first()
        if potravina_objekt:
            potravina_objekt.podoba = 0.0
            print(f"nalezena potravina: {potravina_objekt} z databáze")
        else:
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=potravina,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            potravina_objekt = Potraviny.objects.annotate(podoba=RawSQL(
                "%s::vector <=> embedding", (embedding,))).order_by("podoba").first()
            print(f"Nalezena potravina: {potravina_objekt.nazev}, podoba: {potravina_objekt.podoba}")
        if potravina_objekt.podoba < 0.5:
            makroziviny = potravina_objekt.makroziviny
            kalorie += makroziviny.kalorie*Decimal(koeficient)
            bilkoviny += makroziviny.bilkoviny_gramy*Decimal(koeficient)
            sacharidy += makroziviny.sacharidy_gramy*Decimal(koeficient)
            tuky += makroziviny.tuky_gramy*Decimal(koeficient)
        else:
            raise ValueError("V databázi nebyla nalezena potravina: {potravina}")
    return int(round(kalorie)), round(bilkoviny, 2), round(sacharidy, 2), round(tuky, 2)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = "chat/recepty.json"
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
        for i,item in enumerate(foods):
            print(f"vytvarim potravinu #{i+1}")
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
            Název: {item["nazev"]}
            Ingredience: {", ".join([f'{ingredience["nazev"]}: {ingredience["mnozstvi"]}' for ingredience in item["ingredience"]])}
            Instrukce: {item["instrukce"]}
            Typ jídla: {item["typ_jidla"]}
            Teplota: {item["teplota"]}
            Čas přípravy v minutách: {item["cas_pripravy"]}
            Vhodné pro: {", ".join(item["vhodne_pro"])}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            recept,created = Recepty.objects.get_or_create(
                nazev=item["nazev"],
                ingredience=item["ingredience"],
                instrukce=item["instrukce"],
                typ_jidla=item["typ_jidla"],
                teplota=item["teplota"],
                cas_pripravy_min=item["cas_pripravy"],
                vhodne_pro=item["vhodne_pro"],
                embedding=embedding
            )
            if created:
                kalorie, bilkoviny, sacharidy, tuky = search_recepty(
                    ingredience=item["ingredience"])
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
