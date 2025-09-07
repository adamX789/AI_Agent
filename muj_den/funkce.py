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
    if jednotka in ["ks", "kus", "kusu", "kusy", "kusů"]:
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
    if jednotka in ["ks", "kus", "kusu", "kusy", "kusů"]:
        final_response_kusy: PrevodJednotekKusy = response.parsed
        return final_response_kusy.pocet_gramu_na_kus
    elif jednotka in ["plátek", "plátky", "plátků"]:
        final_response_platky: PrevodJednotekPlatky = response.parsed
        return final_response_platky.pocet_gramu_na_platek


def najdi_potravinu(ingredience, profile):
    for item in ingredience:
        potravina = item["nazev"]
        mnozstvi = item["mnozstvi"]
        if mnozstvi == "špetka":
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
        kusy_platky_list = ["ks", "kus", "kusy", "kusu",
                            "kusů", "plátek", "plátky", "plátků"]
        kila_litry_list = ["kg", "l"]
        if jednotka in kusy_platky_list:
            result = call_llm(potravina=potravina, jednotka=jednotka)
            celkem_gramu = hodnota*result
        elif jednotka in kila_litry_list:
            celkem_gramu = hodnota*1000
        else:
            celkem_gramu = hodnota

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
            print(
                f"Nalezena potravina: {potravina_objekt.nazev}, podoba: {potravina_objekt.podoba}")
        if potravina_objekt.podoba < 0.5:
            jednotka_vysledna = "ml" if jednotka in ["ml", "l"] else "g"
            profile.food_set.create(
                potravina=potravina_objekt, jednotka=jednotka_vysledna, hmotnost_g=Decimal(round(celkem_gramu, 2)))
        else:
            raise ValueError(
                "V databázi nebyla nalezena potravina: {potravina}")


def filtruj_recepty_podle_kcal(kalorie, typ_jidla, seznam_receptu):
    min_kcal = kalorie * Decimal(0.85)
    max_kcal = kalorie * Decimal(1.15)
    seznam_id = [r.id for r in seznam_receptu]
    seznam_receptu = Recepty.objects.filter(id__in = seznam_id)
    relevantni_recepty = seznam_receptu.filter(
        typ_jidla=typ_jidla,
        makrozivinyrecepty__kalorie__gte=min_kcal,
        makrozivinyrecepty__kalorie__lte=max_kcal
    )
    return relevantni_recepty


def vyber_snidani(vsechny_recepty, profile):
    zbyvajici_kalorie = profile.denni_kalorie
    zbyvajici_bilkoviny = profile.denni_bilkoviny
    zbyvajici_sacharidy = profile.denni_sacharidy
    zbyvajici_tuky = profile.denni_tuky
    print(f"""Vyber snidane,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    relevantni_snidane = filtruj_recepty_podle_kcal(
        kalorie=zbyvajici_kalorie*Decimal(0.2), typ_jidla="snidane", seznam_receptu=vsechny_recepty)
    if relevantni_snidane.exists():
        vybrana_snidane = relevantni_snidane.order_by("?").first()
        profile.jidelnicek.seznam_snidani.add(vybrana_snidane)
        dalsi_recepty = relevantni_snidane.exclude(id=vybrana_snidane.id)
        dalsi_snidane = dalsi_recepty.order_by("?")[:3]
        profile.jidelnicek.seznam_snidani.add(*dalsi_snidane)
        profile.vybranerecepty.snidane = vybrana_snidane
        profile.vybranerecepty.save()
    pocet_zbyvajicich = profile.jidelnicek.seznam_snidani.count()

    if pocet_zbyvajicich < 4:
        seznam_id = [s.id for s in profile.jidelnicek.seznam_snidani.all()]
        nove_recepty = Recepty.objects.all().exclude(id__in = seznam_id)
        relevantni_snidane = filtruj_recepty_podle_kcal(
        kalorie=zbyvajici_kalorie*Decimal(0.2), typ_jidla="snidane", seznam_receptu=nove_recepty)
        dalsi_snidane = relevantni_snidane.order_by("?")[:4-pocet_zbyvajicich]
        profile.jidelnicek.seznam_snidani.add(*dalsi_snidane)
        profile.save()
        if not profile.vybranerecepty.snidane and relevantni_snidane.exists():
            profile.vybranerecepty.snidane = dalsi_snidane.first()

    profile.vybranerecepty.save()
    if profile.vybranerecepty.snidane:
        zbyvajici_kalorie -= profile.vybranerecepty.snidane.makrozivinyrecepty.kalorie
        zbyvajici_bilkoviny -= profile.vybranerecepty.snidane.makrozivinyrecepty.bilkoviny_gramy
        zbyvajici_sacharidy -= profile.vybranerecepty.snidane.makrozivinyrecepty.sacharidy_gramy
        zbyvajici_tuky -= profile.vybranerecepty.snidane.makrozivinyrecepty.tuky_gramy
    else:
        print("nebyla nalezena žádná snídaně")
    profile.save()
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_svaciny(vsechny_recepty, cislo_svaciny, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber svaciny {cislo_svaciny},
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    relevantni_svaciny = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.2), typ_jidla="svacina", seznam_receptu=vsechny_recepty)
    if relevantni_svaciny.exists():
        vybrana_svacina = relevantni_svaciny.order_by("?").first()
        if cislo_svaciny == 1:
            profile.vybranerecepty.svacina1 = vybrana_svacina
            profile.jidelnicek.seznam_svacin1.add(vybrana_svacina)
            dalsi_recepty = relevantni_svaciny.exclude(id=vybrana_svacina.id)
            dalsi_svaciny = dalsi_recepty.order_by("?")[:3]
            profile.jidelnicek.seznam_svacin1.add(*dalsi_svaciny)
        else:
            profile.vybranerecepty.svacina2 = vybrana_svacina
            profile.jidelnicek.seznam_svacin2.add(vybrana_svacina)
            dalsi_recepty = relevantni_svaciny.exclude(id=vybrana_svacina.id)
            dalsi_svaciny = dalsi_recepty.order_by("?")[:3]
            profile.jidelnicek.seznam_svacin2.add(*dalsi_svaciny)
        profile.vybranerecepty.save()
        profile.save()
    pocet_zbyvajicich = profile.jidelnicek.seznam_svacin1.count() if cislo_svaciny == 1 else profile.jidelnicek.seznam_svacin2.count()

    if pocet_zbyvajicich < 4:
        seznam_id = [s.id for s in profile.jidelnicek.seznam_svacin1.all()] if cislo_svaciny == 1 else [s.id for s in profile.jidelnicek.seznam_svacin2.all()]
        nove_recepty = Recepty.objects.all().exclude(id__in = seznam_id)
        relevantni_svaciny = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.2), typ_jidla="svacina", seznam_receptu=nove_recepty)
        dalsi_svaciny = relevantni_svaciny.order_by("?")[:4-pocet_zbyvajicich]
        profile.jidelnicek.seznam_svacin1.add(*dalsi_svaciny) if cislo_svaciny == 1 else profile.jidelnicek.seznam_svacin2.add(*dalsi_svaciny)
        profile.save()
        if cislo_svaciny == 1:
            if not profile.vybranerecepty.svacina1 and relevantni_svaciny.exists():
                profile.vybranerecepty.svacina1 = dalsi_svaciny.first()
        else:
            if not profile.vybranerecepty.svacina2 and relevantni_svaciny.exists():
                profile.vybranerecepty.svacina2 = dalsi_svaciny.first()
    profile.vybranerecepty.save()
    if cislo_svaciny == 1:
        if profile.vybranerecepty.svacina1:
            zbyvajici_kalorie -= profile.vybranerecepty.svacina1.makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -=profile.vybranerecepty.svacina1.makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= profile.vybranerecepty.svacina1.makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= profile.vybranerecepty.svacina1.makrozivinyrecepty.tuky_gramy
        else:
            print("nebyla nalezena žádná svačina")
    else:
        if profile.vybranerecepty.svacina2:
            zbyvajici_kalorie -= profile.vybranerecepty.svacina2.makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -=profile.vybranerecepty.svacina2.makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= profile.vybranerecepty.svacina2.makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= profile.vybranerecepty.svacina2.makrozivinyrecepty.tuky_gramy
        else:
            print("nebyla nalezena žádná svačina")
    profile.save()
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_obed(vsechny_recepty, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber obedu,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    relevantni_obedy = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.2), typ_jidla="obed", seznam_receptu=vsechny_recepty)
    if relevantni_obedy.exists():
        vybrany_obed = relevantni_obedy.order_by("?").first()
        profile.jidelnicek.seznam_obedu.add(vybrany_obed)
        dalsi_recepty = relevantni_obedy.exclude(id=vybrany_obed.id)
        dalsi_obedy = dalsi_recepty.order_by("?")[:3]
        profile.jidelnicek.seznam_obedu.add(*dalsi_obedy)
        profile.vybranerecepty.obed = vybrany_obed
        profile.vybranerecepty.save()
        profile.save()
    pocet_zbyvajicich = profile.jidelnicek.seznam_obedu.count()

    if pocet_zbyvajicich < 4:
        seznam_id = [o.id for o in profile.jidelnicek.seznam_obedu.all()]
        nove_recepty = Recepty.objects.all().exclude(id__in = seznam_id)
        relevantni_obedy = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.2), typ_jidla="obed", seznam_receptu=nove_recepty)
        dalsi_obedy = relevantni_obedy.order_by("?")[:4-pocet_zbyvajicich]
        profile.jidelnicek.seznam_obedu.add(*dalsi_obedy)
        profile.save()
        if not profile.vybranerecepty.obed and relevantni_obedy.exists():
            profile.vybranerecepty.obed = dalsi_obedy.first()
    profile.vybranerecepty.save()
    if profile.vybranerecepty.obed:
        zbyvajici_kalorie -= profile.vybranerecepty.obed.makrozivinyrecepty.kalorie
        zbyvajici_bilkoviny -= profile.vybranerecepty.obed.makrozivinyrecepty.bilkoviny_gramy
        zbyvajici_sacharidy -= profile.vybranerecepty.obed.makrozivinyrecepty.sacharidy_gramy
        zbyvajici_tuky -= profile.vybranerecepty.obed.makrozivinyrecepty.tuky_gramy
    else:
        print("nebyl nalezen žádný oběd")
    profile.save()
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_veceri(vsechny_recepty, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber vecere,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    relevantni_vecere = filtruj_recepty_podle_kcal(
        kalorie=Decimal(zbyvajici_kalorie), typ_jidla="vecere", seznam_receptu=vsechny_recepty)
    if relevantni_vecere.exists():
        vybrana_vecere = relevantni_vecere.order_by("?").first()
        profile.jidelnicek.seznam_veceri.add(vybrana_vecere)
        dalsi_recepty = relevantni_vecere.exclude(id=vybrana_vecere.id)
        dalsi_vecere = dalsi_recepty.order_by("?")[:3]
        profile.jidelnicek.seznam_veceri.add(*dalsi_vecere)
        profile.vybranerecepty.vecere = vybrana_vecere
        profile.vybranerecepty.save()
        profile.save()
    pocet_zbyvajicich = profile.jidelnicek.seznam_veceri.count()

    if pocet_zbyvajicich < 4:
        seznam_id = [v.id for v in profile.jidelnicek.seznam_veceri.all()]
        nove_recepty = Recepty.objects.all().exclude(id__in = seznam_id)
        relevantni_vecere = filtruj_recepty_podle_kcal(
        kalorie=Decimal(zbyvajici_kalorie), typ_jidla="vecere", seznam_receptu=nove_recepty)
        dalsi_vecere = relevantni_vecere.order_by("?")[:4-pocet_zbyvajicich]
        profile.jidelnicek.seznam_veceri.add(*dalsi_vecere)
        profile.save()
        if not profile.vybranerecepty.vecere and relevantni_vecere.exists():
            profile.vybranerecepty.vecere = dalsi_vecere.first()

    profile.vybranerecepty.save()
    if profile.vybranerecepty.vecere:
        zbyvajici_kalorie -= profile.vybranerecepty.vecere.makrozivinyrecepty.kalorie
        zbyvajici_bilkoviny -= profile.vybranerecepty.vecere.makrozivinyrecepty.bilkoviny_gramy
        zbyvajici_sacharidy -= profile.vybranerecepty.vecere.makrozivinyrecepty.sacharidy_gramy
        zbyvajici_tuky -= profile.vybranerecepty.vecere.makrozivinyrecepty.tuky_gramy
    else:
        print("nebyla nalezena žádná večeře")
    profile.save()
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def sestav_jidelnicek(profile, reset=False, vsechny_recepty=Recepty.objects.all()):
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
    if reset:
        vybrane_recepty.snidane_snezena, vybrane_recepty.svacina1_snezena, vybrane_recepty.obed_snezen, vybrane_recepty.svacina2_snezena, vybrane_recepty.vecere_snezena = False, False, False, False, False
    vybrane_recepty.save()
    kalorie, bilkoviny, sacharidy, tuky = vyber_snidani(
        vsechny_recepty=vsechny_recepty, profile=profile)
    kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
        vsechny_recepty=vsechny_recepty, profile=profile, cislo_svaciny=1, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_obed(
        vsechny_recepty=vsechny_recepty, profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
        vsechny_recepty=vsechny_recepty, profile=profile, cislo_svaciny=2, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    kalorie, bilkoviny, sacharidy, tuky = vyber_veceri(
        vsechny_recepty=vsechny_recepty, profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
