from django.db.models.expressions import RawSQL
from .models import *
from user_profile.models import Food
from google.genai import types
from muj_den.funkce import call_llm


def search_potraviny_and_update(profile, foods, client):
    dict_list = []
    for item in foods.seznam_jidla:
        nazev_potraviny = item.potravina
        hmotnost = item.hmotnost
        jednotka = item.jednotka
        if jednotka in ["ks","plátky"]:
            odpoved = call_llm(potravina=nazev_potraviny,jednotka=jednotka)
            vysledna_hmotnost=hmotnost*odpoved
            vysledna_jednotka = "g"
        else:
            vysledna_hmotnost = hmotnost
            vysledna_jednotka = jednotka
        potravina_objekt = Potraviny.objects.filter(nazev=nazev_potraviny).first()
        if potravina_objekt:
            print(f"potravina {potravina_objekt.nazev} nalezena v databázi")
            potravina_objekt.podoba = 0.0
        else:
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=nazev_potraviny,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            potravina_objekt = Potraviny.objects.annotate(podoba=RawSQL(
                "%s::vector <=> embedding", (embedding,))).order_by("podoba").first()
        if potravina_objekt.podoba < 0.5:
            makroziviny = potravina_objekt.makroziviny
            print(
                f"potravina: {potravina_objekt.nazev}, podoba: {potravina_objekt.podoba}")
            dict_list.append(
                {
                    "nazev": potravina_objekt.nazev,
                    "popis": potravina_objekt.popis,
                    "hmotnost_v_gramech": vysledna_hmotnost,
                    "kalorie": makroziviny.kalorie,
                    "bilkoviny_na_100g": str(makroziviny.bilkoviny_gramy),
                    "sacharidy_na_100g": str(makroziviny.sacharidy_gramy),
                    "tuky_na_100g": str(makroziviny.tuky_gramy),
                    "vyhody": potravina_objekt.vyhody,
                    "nejlepsi_pro": potravina_objekt.nejlepsi_pro,
                    "nekonzumujte_pokud": potravina_objekt.nekonzumujte_pokud
                }
            )
            profile.food_set.create(
                potravina=potravina_objekt, hmotnost_g=vysledna_hmotnost, jednotka=vysledna_jednotka)
    return dict_list


def nevim(profile, user_embedding, update: bool, pocet_vysledku=3):
    nejrelevantnejsi_potraviny = Potraviny.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for potravina in nejrelevantnejsi_potraviny:
        if potravina.podoba < 0.35:
            makroziviny = Makroziviny.objects.get(potravina=potravina)
            print(f"potravina: {potravina.nazev}, podoba: {potravina.podoba}")
            dict_list.append(
                {
                    "nazev": potravina.nazev,
                    "popis": potravina.popis,
                    "kalorie": makroziviny.kalorie,
                    "bilkoviny_gramy": str(makroziviny.bilkoviny_gramy),
                    "sacharidy_gramy": str(makroziviny.sacharidy_gramy),
                    "tuky_gramy": str(makroziviny.tuky_gramy),
                    "vyhody": potravina.vyhody,
                    "nejlepsi_pro": potravina.nejlepsi_pro,
                    "nekonzumujte_pokud": potravina.nekonzumujte_pokud
                }
            )
    if update:
        for potravina in nejrelevantnejsi_potraviny:
            if potravina.podoba < 0.35:
                profile.food_set.create(potravina=potravina)
    return dict_list

def search_potraviny(user_embedding,pocet_vysledku):
    nejrelevantnejsi_potraviny = Potraviny.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for potravina in nejrelevantnejsi_potraviny:
        if potravina.podoba < 0.35:
            makroziviny = Makroziviny.objects.get(potravina=potravina)
            print(f"potravina: {potravina.nazev}, podoba: {potravina.podoba}")
            dict_list.append(
                {
                    "nazev": potravina.nazev,
                    "popis": potravina.popis,
                    "kalorie": makroziviny.kalorie,
                    "bilkoviny_gramy": str(makroziviny.bilkoviny_gramy),
                    "sacharidy_gramy": str(makroziviny.sacharidy_gramy),
                    "tuky_gramy": str(makroziviny.tuky_gramy),
                    "vyhody": potravina.vyhody,
                    "nejlepsi_pro": potravina.nejlepsi_pro,
                    "nekonzumujte_pokud": potravina.nekonzumujte_pokud
                }
            )
    return dict_list

def search_diety(user_embedding,pocet_vysledku):
    nejrelevantnejsi_diety = Diety.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for dieta in nejrelevantnejsi_diety:
        if dieta.podoba < 0.35:
            print(f"dieta: {dieta.nazev_diety}, podoba: {dieta.podoba}")
            dict_list.append(
                {
                    "nazev": dieta.nazev_diety,
                    "popis": dieta.popis,
                    "vyhody":dieta.vyhody,
                    "neni_doporuceno_pro":dieta.neni_doporuceno_pro
                }
            )
    return dict_list

def search_recepty(user_embedding,pocet_vysledku):
    nejrelevantnejsi_recepty = Recepty.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for recept in nejrelevantnejsi_recepty:
        if recept.podoba < 0.35:
            print(f"recept: {recept.nazev}, podoba: {recept.podoba}")
            dict_list.append(
                {
                    "nazev": recept.nazev,
                    "ingredience":recept.ingredience,
                    "instrukce": recept.instrukce,
                    "typ_jidla":recept.typ_jidla,
                    "teplota":recept.teplota,
                    "cas_pripravy_v_min":recept.cas_pripravy_min,
                    "vhodne_pro":recept.vhodne_pro,
                }
            )
    return dict_list

def search_situace(user_embedding,pocet_vysledku):
    nejrelevantnejsi_situace = Situace.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for situace in nejrelevantnejsi_situace:
        if situace.podoba < 0.35:
            print(f"situace: {situace.popis_situace}, podoba: {situace.podoba}")
            dict_list.append(
                {
                    "popis_situace": situace.popis_situace,
                    "rada":situace.rada
                }
            )
    return dict_list