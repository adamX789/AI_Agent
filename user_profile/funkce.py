from decimal import Decimal
import os
import math
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"


class UrceniBodyfat(BaseModel):
    lze_urcit_procento_telesneho_tuku: bool = Field(
        description="Jestli lze z obrázku určit procento tělesného tuku")
    procento_telesneho_tuku: float = Field(
        description="Procento tělesného tuku osoby na obrázku v desetinném čísle.")
    duvod: str = Field(
        description="Důvod, podle kterého jsi se rozhodl pro tuto hodnotu.")


def get_bmr_simple(pohlavi, vek, vyska, vaha):
    print("vykonavam funkci pro bmr")
    if pohlavi == "Muž":
        bmr = Decimal(88.362) + (Decimal(13.397)*vaha) + \
            (Decimal(4.799)*vyska) - (Decimal(5.677)*vek)
    else:
        bmr = Decimal(447.593) + (Decimal(9.247)*vaha) + \
            (Decimal(3.098)*vyska) - (Decimal(4.330)*vek)
    return float(bmr)


def get_bf_by_measures(pohlavi, pas, krk, boky, vyska):
    if pohlavi == "Muž":
        if pas <= krk:
            return -1
        bf_percent = 495 / (1.0324 - 0.19077*math.log10(float(pas-krk)
                                                        ) + 0.15456*math.log10(float(vyska))) - 450
    else:
        if pas+boky <= krk:
            return -1
        bf_percent = 495 / (1.29579 - 0.35004*math.log10(float(pas +
                            boky-krk)) + 0.22100*math.log10(float(vyska))) - 450
    print(bf_percent)
    return Decimal(round(bf_percent, 2))


def get_bf_by_image(image_bytes, mime_type):
    contents = types.Content(role="user", parts=[
                             types.Part.from_bytes(data=image_bytes, mime_type=mime_type)])
    config = types.GenerateContentConfig(system_instruction="Analyzuj následující obrázek. Pokud je na něm osoba, která je zobrazena celá a v takové pozici, ze které lze odhadnout procento tělesného tuku, proveď tento odhad a výsledek vlož do pole 'procento_telesneho_tuku'. Pokud obrázek nesplňuje tyto podmínky (např. je na něm pes, krajina, nebo osoba v oblečení) vlož do pole 'procento_telesneho_tuku' hodnotu 0. Uveď stručný důvod pro své rozhodnutí", response_schema=UrceniBodyfat, response_mime_type="application/json")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    formatted_response: UrceniBodyfat = response.parsed
    print(formatted_response)
    if not formatted_response.lze_urcit_procento_telesneho_tuku:
        return -1
    return Decimal(round(formatted_response.procento_telesneho_tuku, 2))


def get_lbm(vaha, bodyfat):
    lbm = float(vaha) * ((100-float(bodyfat))/100)
    return lbm


def get_bmr_advanced(lbm):
    bmr = 370 + (21.6*lbm)
    return bmr


def get_tdee(bmr, vek, aktivita):
    print("vykonavam funkci pro tdee")
    if aktivita == "Sedavý":
        tdee = bmr*1.1
        return tdee

    if vek < 35:
        if aktivita == "Lehká aktivita":
            tdee = bmr*1.25
        elif aktivita == "Střední aktivita":
            tdee = bmr*1.35
        elif aktivita == "Vysoká aktivita":
            tdee = bmr*1.5
        else:
            tdee = bmr*1.7
    else:
        if aktivita == "Lehká aktivita":
            tdee = bmr*1.2
        elif aktivita == "Střední aktivita":
            tdee = bmr*1.3
        elif aktivita == "Vysoká aktivita":
            tdee = bmr*1.4
        else:
            tdee = bmr*1.5

    return tdee


def get_cals_cut(tdee, bmr, x):
    print("vykonavam funkci pro kalorie cut")
    deficit = (tdee-bmr)*x
    kalorie = tdee-deficit
    return int(round(kalorie))


def get_cals_bulk(tdee, yes_count):
    print("vykonavam funkci pro kalorie bulk")
    if yes_count == 3:
        kalorie = tdee*1.2
    elif yes_count == 2:
        kalorie = tdee*1.15
    elif yes_count == 1:
        kalorie = tdee*1.1
    else:
        kalorie = tdee*1.05
    return int(round(kalorie))


def get_macros_simple(cals, vaha):
    print("vykonavam funkci pro makra")
    denni_bilkoviny = int(round(vaha*2))
    denni_tuky = int(round((cals*0.25)/9))
    denni_sacharidy = int(
        round((cals - (denni_bilkoviny*4) - (denni_tuky*9))/4))
    pitny_rezim = round((vaha*Decimal(37.5))/1000, 2)
    return denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim


def get_macros_advanced(cals, lbm, vaha, aktivita, vek):
    if vek < 35:
        if aktivita == "Sedavý":
            bilkoviny = int(round(lbm*1.8))
            tuky = int(round(lbm*1.3))
        if aktivita == "Lehká aktivita":
            bilkoviny = int(round(lbm*2))
            tuky = int(round(lbm*1.2))
        elif aktivita == "Střední aktivita":
            bilkoviny = int(round(lbm*2.4))
            tuky = int(round(lbm*1.1))
        elif aktivita == "Vysoká aktivita":
            bilkoviny = int(round(lbm*2.7))
            tuky = int(round(lbm*1))
        else:
            bilkoviny = int(round(lbm*3))
            tuky = int(round(lbm*0.8))
    else:
        if aktivita == "Sedavý":
            bilkoviny = int(round(lbm*1.6))
            tuky = int(round(lbm*1.3))
        if aktivita == "Lehká aktivita":
            bilkoviny = int(round(lbm*1.9))
            tuky = int(round(lbm*1.2))
        elif aktivita == "Střední aktivita":
            bilkoviny = int(round(lbm*2.2))
            tuky = int(round(lbm*1.1))
        elif aktivita == "Vysoká aktivita":
            bilkoviny = int(round(lbm*2.4))
            tuky = int(round(lbm*1))
        else:
            bilkoviny = int(round(lbm*2.6))
            tuky = int(round(lbm*0.8))
    sacharidy = int(round((cals - (bilkoviny*4) - (tuky*9))/4))
    pitny_rezim = round((vaha*Decimal(37.5))/1000, 2)
    return bilkoviny, sacharidy, tuky, pitny_rezim
