from chat.models import Recepty
from user_profile.models import Profile
from muj_den.models import JidelnicekRecept
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


def zvetsi_zmensi_recept(min_k, max_k, recept_k):
    cilove_k = (min_k + max_k) / 2
    scale_factor = cilove_k / Decimal(recept_k)
    return round(scale_factor,3)


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
    recepty_dict = []
    seznam_id1 = [r.id for r in seznam_receptu]
    seznam_receptu = Recepty.objects.filter(id__in=seznam_id1)
    vsechny_rec_podle_typu = seznam_receptu.filter(typ_jidla=typ_jidla)
    relevantni_recepty = vsechny_rec_podle_typu.filter(
        makrozivinyrecepty__kalorie__gte=min_kcal,
        makrozivinyrecepty__kalorie__lte=max_kcal
    ).order_by("?")[:4]
    for recept in relevantni_recepty:
        recepty_dict.append({
            "recept": recept,
            "scale_factor": Decimal(1),
            "chod": typ_jidla
        })

    if len(recepty_dict) < 4:
        seznam_id = [r.id for r in relevantni_recepty]
        zbyvajici_recepty = vsechny_rec_podle_typu.exclude(
            id__in=seznam_id).order_by("?")[:4 - len(recepty_dict)]
        for recept in zbyvajici_recepty:
            recepty_dict.append({
                "recept": recept,
                "scale_factor": zvetsi_zmensi_recept(min_k=min_kcal, max_k=max_kcal, recept_k=recept.makrozivinyrecepty.kalorie),
                "chod": typ_jidla
            })

    if len(recepty_dict) < 4:
        seznam_id.extend(r.id for r in zbyvajici_recepty)
        zbyvajici_recepty = Recepty.objects.filter(
            typ_jidla=typ_jidla).exclude(id__in=seznam_id)
        relevantni_recepty2 = zbyvajici_recepty.filter(
            makrozivinyrecepty__kalorie__gte=min_kcal,
            makrozivinyrecepty__kalorie__lte=max_kcal
        ).order_by("?")[:4 - len(recepty_dict)]
        for recept in relevantni_recepty2:
            recepty_dict.append({
                "recept": recept,
                "scale_factor": Decimal(1),
                "chod": typ_jidla
            })

    if len(recepty_dict) < 4:
        seznam_id.extend(r.id for r in relevantni_recepty2)
        zbyvajici_recepty2 = Recepty.objects.filter(typ_jidla=typ_jidla).exclude(
            id__in=seznam_id).order_by("?")[:4 - len(recepty_dict)]
        for recept in zbyvajici_recepty2:
            recepty_dict.append({
                "recept": recept,
                "scale_factor": zvetsi_zmensi_recept(min_k=min_kcal, max_k=max_kcal, recept_k=recept.makrozivinyrecepty.kalorie),
                "chod": typ_jidla
            })
    return recepty_dict


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
    jidelnicek,_ = Jidelnicek.objects.get_or_create(profile=profile)
    vybrane_snidane = filtruj_recepty_podle_kcal(
        kalorie=zbyvajici_kalorie*Decimal(0.2), typ_jidla="snidane", seznam_receptu=vsechny_recepty)
    for i,snidane in enumerate(vybrane_snidane):
        recept,created = JidelnicekRecept.objects.get_or_create(
            jidelnicek=jidelnicek,
            recept = snidane["recept"],
            scale_factor = snidane["scale_factor"],
            chod = snidane["chod"],
            snezeno = False
        )
        if i == 0:
            zbyvajici_kalorie -= snidane["recept"].makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -= snidane["recept"].makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= snidane["recept"].makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= snidane["recept"].makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_svaciny(vsechny_recepty, cislo_svaciny, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber svaciny {cislo_svaciny},
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    jidelnicek = Jidelnicek.objects.get(profile=profile)
    vybrane_svaciny = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.125), typ_jidla="svacina", seznam_receptu=vsechny_recepty)
    for i,svacina in enumerate(vybrane_svaciny):
        JidelnicekRecept.objects.create(
            jidelnicek=jidelnicek,
            recept = svacina["recept"],
            scale_factor = svacina["scale_factor"],
            chod = "svacina1" if cislo_svaciny == 1 else "svacina2",
            snezeno = False
        )
        if i == 0:
            zbyvajici_kalorie -= svacina["recept"].makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -= svacina["recept"].makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= svacina["recept"].makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= svacina["recept"].makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_obed(vsechny_recepty, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber obedu,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    jidelnicek = Jidelnicek.objects.get(profile=profile)
    vybrane_obedy = filtruj_recepty_podle_kcal(
        kalorie=profile.denni_kalorie*Decimal(0.3), typ_jidla="obed", seznam_receptu=vsechny_recepty)
    for i,obed in enumerate(vybrane_obedy):
        JidelnicekRecept.objects.create(
            jidelnicek=jidelnicek,
            recept = obed["recept"],
            scale_factor = obed["scale_factor"],
            chod = obed["chod"],
            snezeno = False
        )
        if i == 0:
            zbyvajici_kalorie -= obed["recept"].makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -= obed["recept"].makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= obed["recept"].makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= obed["recept"].makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def vyber_veceri(vsechny_recepty, profile, zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky):
    print(f"""Vyber vecere,
zbyvajici kalorie = {zbyvajici_kalorie}
zbyvajici bilkoviny = {zbyvajici_bilkoviny}
zbyvajici sacharidy = {zbyvajici_sacharidy}
zbyvajici tuky = {zbyvajici_tuky}""")
    jidelnicek = Jidelnicek.objects.get(profile=profile)
    vybrane_vecere = filtruj_recepty_podle_kcal(
        kalorie=Decimal(zbyvajici_kalorie), typ_jidla="vecere", seznam_receptu=vsechny_recepty)
    for i,vecere in enumerate(vybrane_vecere):
        JidelnicekRecept.objects.create(
            jidelnicek=jidelnicek,
            recept = vecere["recept"],
            scale_factor = vecere["scale_factor"],
            chod = vecere["chod"],
            snezeno = False
        )
        if i == 0:
            zbyvajici_kalorie -= vecere["recept"].makrozivinyrecepty.kalorie
            zbyvajici_bilkoviny -= vecere["recept"].makrozivinyrecepty.bilkoviny_gramy
            zbyvajici_sacharidy -= vecere["recept"].makrozivinyrecepty.sacharidy_gramy
            zbyvajici_tuky -= vecere["recept"].makrozivinyrecepty.tuky_gramy
    return zbyvajici_kalorie, zbyvajici_bilkoviny, zbyvajici_sacharidy, zbyvajici_tuky


def sestav_jidelnicek(profile, reset=False, vsechny_recepty=Recepty.objects.all()):
    kalorie = profile.denni_kalorie
    bilkoviny = profile.denni_bilkoviny
    sacharidy = profile.denni_sacharidy
    tuky = profile.denni_tuky
    jidelnicek,_= Jidelnicek.objects.get_or_create(profile=profile)
    if reset:
        JidelnicekRecept.objects.all().delete()
        snedena_list = []
    else:
        snedena_jidla = jidelnicek.jidelnicekrecept_set.filter(snezeno=True)
        snedena_list = [s.chod for s in snedena_jidla]
        jidelnicek.jidelnicekrecept_set.filter(snezeno=False).delete()
    if "snidane" not in snedena_list:
        kalorie, bilkoviny, sacharidy, tuky = vyber_snidani(
            vsechny_recepty=vsechny_recepty, profile=profile)
    else:
        snedena_snidane = snedena_jidla.get(chod = "snidane")
        kalorie -= snedena_snidane.recept.makrozivinyrecepty.kalorie*snedena_snidane.scale_factor
        bilkoviny -= snedena_snidane.recept.makrozivinyrecepty.bilkoviny_gramy*snedena_snidane.scale_factor
        sacharidy -= snedena_snidane.recept.makrozivinyrecepty.sacharidy_gramy*snedena_snidane.scale_factor
        tuky -= snedena_snidane.recept.makrozivinyrecepty.tuky_gramy*snedena_snidane.scale_factor
    if "svacina1" not in snedena_list:
        kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
            vsechny_recepty=vsechny_recepty, profile=profile, cislo_svaciny=1, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    else:
        snedena_svacina1 = snedena_jidla.get(chod = "svacina1")
        kalorie -= snedena_svacina1.recept.makrozivinyrecepty.kalorie*snedena_svacina1.scale_factor
        bilkoviny -= snedena_svacina1.recept.makrozivinyrecepty.bilkoviny_gramy*snedena_svacina1.scale_factor
        sacharidy -= snedena_svacina1.recept.makrozivinyrecepty.sacharidy_gramy*snedena_svacina1.scale_factor
        tuky -= snedena_svacina1.recept.makrozivinyrecepty.tuky_gramy*snedena_svacina1.scale_factor
    if "obed" not in snedena_list:
        kalorie, bilkoviny, sacharidy, tuky = vyber_obed(
            vsechny_recepty=vsechny_recepty, profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    else:
        snedeny_obed = snedena_jidla.get(chod = "obed")
        kalorie -= snedeny_obed.recept.makrozivinyrecepty.kalorie*snedeny_obed.scale_factor
        bilkoviny -= snedeny_obed.recept.makrozivinyrecepty.bilkoviny_gramy*snedeny_obed.scale_factor
        sacharidy -= snedeny_obed.recept.makrozivinyrecepty.sacharidy_gramy*snedeny_obed.scale_factor
        tuky -= snedeny_obed.recept.makrozivinyrecepty.tuky_gramy*snedeny_obed.scale_factor
    if "svacina2" not in snedena_list:
        kalorie, bilkoviny, sacharidy, tuky = vyber_svaciny(
            vsechny_recepty=vsechny_recepty, profile=profile, cislo_svaciny=2, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    else:
        snedena_svacina2 = snedena_jidla.get(chod = "svacina2")
        kalorie -= snedena_svacina2.recept.makrozivinyrecepty.kalorie*snedena_svacina2.scale_factor
        bilkoviny -= snedena_svacina2.recept.makrozivinyrecepty.bilkoviny_gramy*snedena_svacina2.scale_factor
        sacharidy -= snedena_svacina2.recept.makrozivinyrecepty.sacharidy_gramy*snedena_svacina2.scale_factor
        tuky -= snedena_svacina2.recept.makrozivinyrecepty.tuky_gramy*snedena_svacina2.scale_factor
    if "vecere" not in snedena_list:
        kalorie, bilkoviny, sacharidy, tuky = vyber_veceri(
            vsechny_recepty=vsechny_recepty, profile=profile, zbyvajici_kalorie=kalorie, zbyvajici_bilkoviny=bilkoviny, zbyvajici_sacharidy=sacharidy, zbyvajici_tuky=tuky)
    else:
        snedena_vecere = snedena_jidla.get(chod = "vecere")
        kalorie -= snedena_vecere.recept.makrozivinyrecepty.kalorie*snedena_vecere.scale_factor
        bilkoviny -= snedena_vecere.recept.makrozivinyrecepty.bilkoviny_gramy*snedena_vecere.scale_factor
        sacharidy -= snedena_vecere.recept.makrozivinyrecepty.sacharidy_gramy*snedena_vecere.scale_factor
        tuky -= snedena_vecere.recept.makrozivinyrecepty.tuky_gramy*snedena_vecere.scale_factor
