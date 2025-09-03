from chat.models import Recepty
from user_profile.models import Profile
from .models import *
from decimal import Decimal
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from chat.models import Potraviny
from django.db.models.expressions import RawSQL

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"


class PrevodJednotekKusy(BaseModel):
    pocet_gramu_na_kus: float = Field(
        description="Kolik gramů má 1 kus dané potraviny.")


class PrevodJednotekPlatky(BaseModel):
    pocet_gramu_na_platek: float = Field(
        description="Kolik gramů má 1 plátek dané potraviny.")


def call_llm(potravina, jednotka):
    contents = types.Content(
        role="user", parts=[types.Part(text=f"Potravina: {potravina}")])
    if jednotka in ["ks", "kus", "kusy", "kusů"]:
        config = types.GenerateContentConfig(system_instruction="Jsi expert na převod jednotek jídla. Tvým úkolem je zjistit, kolik gramů má 1 kus dané potraviny",
                                             response_schema=PrevodJednotekKusy, response_mime_type="application/json")
    elif jednotka in ["plátek", "plátky", "plátků"]:
        config = types.GenerateContentConfig(system_instruction="Jsi expert na převod jednotek jídla. Tvým úkolem je zjistit, kolik gramů má 1 plátek dané potraviny",
                                             response_schema=PrevodJednotekPlatky, response_mime_type="application/json")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )
    if jednotka in ["ks", "kus", "kusy", "kusů"]:
        final_response_kusy: PrevodJednotekKusy = response.parsed
        return final_response_kusy.pocet_gramu_na_kus
    elif jednotka in ["plátek", "plátky", "plátků"]:
        final_response_platky: PrevodJednotekPlatky = response.parsed
        return final_response_platky.pocet_gramu_na_platek


def najdi_potravinu(ingredience, profile):
    for item in ingredience:
        potravina = item["nazev"]
        mnozstvi = item["mnozstvi"]
        print(f"hledam potravinu: {potravina}")
        casti = mnozstvi.strip().split(" ")
        hodnota = float(casti[0])
        jednotka = casti[1].lower()
        kusy_platky_list = ["ks", "kus", "kusy",
                            "kusů", "plátek", "plátky", "plátků"]
        kila_litry_list = ["kg", "l"]
        if jednotka in kusy_platky_list:
            result = call_llm(potravina=potravina, jednotka=jednotka)
            celkem_gramu = hodnota*result
        elif jednotka in kila_litry_list:
            celkem_gramu = hodnota*1000
        else:
            celkem_gramu = hodnota

        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=potravina,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        embedding = response.embeddings[0].values
        potravina_objekt = Potraviny.objects.annotate(podoba=RawSQL(
            "%s::vector <=> embedding", (embedding,))).order_by("podoba").first()
        print(
            f"Nalezena potravina: {potravina_objekt.nazev}, podoba: {potravina_objekt.podoba}")
        if potravina_objekt.podoba < 0.5:
            jednotka_vysledna = "ml" if jednotka in ["ml", "l"] else "g"
            profile.food_set.create(
                potravina=potravina_objekt, jednotka=jednotka_vysledna, hmotnost_g=Decimal(round(celkem_gramu, 2)))
        else:
            raise ValueError(
                "V databázi nebyla nalezena potravina: {potravina}")


def vyber_snidani(profile):
    zbyvajici_kalorie = profile.denni_kalorie
    zbyvajici_bilkoviny = profile.denni_bilkoviny
    zbyvajici_sacharidy = profile.denni_sacharidy
    zbyvajici_tuky = profile.denni_tuky
    print(f"""Vyber snidane,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    vsechny_snidane = Recepty.objects.filter(typ_jidla="snidane")
    vybrana_snidane = vsechny_snidane.order_by("?").first()
    profile.vybranerecepty.snidane = vybrana_snidane
    profile.vybranerecepty.save()
    profile.jidelnicek.seznam_snidani.add(vybrana_snidane)
    dalsi_recepty = vsechny_snidane.exclude(id=vybrana_snidane.id)
    dalsi_snidane = dalsi_recepty.order_by("?").first()
    if dalsi_snidane:
        profile.jidelnicek.seznam_snidani.add(dalsi_snidane)
    else:
        print("V databázi nebyla nalezena žádná další snídaně")
    profile.save()
    zbyvajici_kalorie -= vybrana_snidane.makrozivinyrecepty.kalorie
    zbyvajici_bilkoviny -= vybrana_snidane.makrozivinyrecepty.bilkoviny_gramy
    zbyvajici_sacharidy -= vybrana_snidane.makrozivinyrecepty.sacharidy_gramy
    zbyvajici_tuky -= vybrana_snidane.makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_svaciny(cislo_svaciny, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber svaciny,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    vsechny_svaciny = Recepty.objects.filter(typ_jidla="svacina")
    vybrana_svacina = vsechny_svaciny.order_by("?").first()
    if cislo_svaciny == 1:
        profile.vybranerecepty.svacina1 = vybrana_svacina
        profile.jidelnicek.seznam_svacin1.add(vybrana_svacina)
    else:
        profile.vybranerecepty.svacina2 = vybrana_svacina
        profile.jidelnicek.seznam_svacin2.add(vybrana_svacina)
    profile.vybranerecepty.save()
    dalsi_recepty = vsechny_svaciny.exclude(id=vybrana_svacina.id)
    dalsi_svaciny = dalsi_recepty.order_by("?")[:2]
    if cislo_svaciny == 1:
        profile.jidelnicek.seznam_svacin1.add(*dalsi_svaciny)
    else:
        profile.jidelnicek.seznam_svacin2.add(*dalsi_svaciny)
    zbyvajici_kalorie -= vybrana_svacina.makrozivinyrecepty.kalorie
    zbyvajici_bilkoviny -= vybrana_svacina.makrozivinyrecepty.bilkoviny_gramy
    zbyvajici_sacharidy -= vybrana_svacina.makrozivinyrecepty.sacharidy_gramy
    zbyvajici_tuky -= vybrana_svacina.makrozivinyrecepty.tuky_gramy
    profile.save()
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_obed(profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber obeda,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    vsechny_obedy = Recepty.objects.filter(typ_jidla="obed")
    vybrany_obed = vsechny_obedy.order_by("?").first()
    profile.vybranerecepty.obed = vybrany_obed
    profile.vybranerecepty.save()
    profile.jidelnicek.seznam_obedu.add(vybrany_obed)
    dalsi_recepty = vsechny_obedy.exclude(id=vybrany_obed.id)
    dalsi_obed = dalsi_recepty.order_by("?").first()
    if dalsi_obed:
        profile.jidelnicek.seznam_obedu.add(dalsi_obed)
    else:
        print("V databázi nebyla nalezena žádná další snídaně")
    profile.save()
    zbyvajici_kalorie -= vybrany_obed.makrozivinyrecepty.kalorie
    zbyvajici_bilkoviny -= vybrany_obed.makrozivinyrecepty.bilkoviny_gramy
    zbyvajici_sacharidy -= vybrany_obed.makrozivinyrecepty.sacharidy_gramy
    zbyvajici_tuky -= vybrany_obed.makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_veceri(profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber vecere,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    vsechny_vecere = Recepty.objects.filter(typ_jidla="vecere")
    vybrana_vecere = vsechny_vecere.order_by("?").first()
    profile.vybranerecepty.vecere = vybrana_vecere
    profile.vybranerecepty.save()
    profile.jidelnicek.seznam_veceri.add(vybrana_vecere)
    dalsi_recepty = vsechny_vecere.exclude(id=vybrana_vecere.id)
    dalsi_vecere = dalsi_recepty.order_by("?").first()
    if dalsi_vecere:
        profile.jidelnicek.seznam_veceri.add(dalsi_vecere)
    else:
        print("V databázi nebyla nalezena žádná další snídaně")
    profile.save()
    zbyvajici_kalorie -= vybrana_vecere.makrozivinyrecepty.kalorie
    zbyvajici_bilkoviny -= vybrana_vecere.makrozivinyrecepty.bilkoviny_gramy
    zbyvajici_sacharidy -= vybrana_vecere.makrozivinyrecepty.sacharidy_gramy
    zbyvajici_tuky -= vybrana_vecere.makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def sestav_jidelnicek(profile,reset=False):
    vybrane_recepty, _ = VybraneRecepty.objects.get_or_create(profile=profile)
    jidelnicek, _ = Jidelnicek.objects.get_or_create(profile=profile)
    vybrane_recepty.snidane = None
    vybrane_recepty.svacina1 = None
    vybrane_recepty.obed = None
    vybrane_recepty.svacina2 = None
    vybrane_recepty.vecere = None
    jidelnicek.seznam_snidani.clear()
    jidelnicek.seznam_svacin1.clear()
    jidelnicek.seznam_obedu.clear()
    jidelnicek.seznam_svacin2.clear()
    jidelnicek.seznam_veceri.clear()
    vybrane_recepty.save()
    if reset:
        vybrane_recepty.snidane_snezena,vybrane_recepty.svacina1_snezena,vybrane_recepty.obed_snezen,vybrane_recepty.svacina2_snezena,vybrane_recepty.vecere_snezena = False,False,False,False,False
    kalorie, bilkoviny, sacharidy, tuky = vyber_snidani(profile=profile)
    kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
        profile=profile, cislo_svaciny=1, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_obed(
        profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
        profile=profile, cislo_svaciny=2, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_veceri(
        profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
