import pathlib
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import Literal
from .tools import search_potraviny

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
file = pathlib.Path("chat/vyzivovy_specialista.pdf")
model = "gemini-2.5-flash"


class PrvniUrceniVstupu(BaseModel):
    """
    Určí, zda se dotaz vůbec týká výživy
    """
    tyka_se_vyzivy: bool = Field(
        description="Jestli se zadaný text týká výživy")
    skore_jistoty: float = Field(
        description="Skóre jistoty mezi 0 a 1, 0 znamená, že si nejsi vůbec jistý svým rozhodnutím, 1 znamená, že si jsi úplně jistý svým rozhodnutím")
    duvod: str = Field(description="Důvod, podle kterého jsi se rozhodl")


class UrceniVetaOtazka(BaseModel):
    """
    Určí, zda se jedná o větu nebo otázku
    """
    typ_textu: Literal["otazka", "oznameni"] = Field(
        description="Urči, jestli je text otázka o jídle, nebo jen oznámení o tom, co uživatel snědl")
    skore_jistoty: float = Field(
        description="Skóre jistoty mezi 0 a 1, 0 znamená, že si nejsi vůbec jistý svým rozhodnutím, 1 znamená, že si jsi úplně jistý svým rozhodnutím")
    duvod: str = Field(description="Důvod, podle kterého jsi se rozhodl")


class UrceniTypuOtazky(BaseModel):
    """
    Určí, jaké oblasti výživy se dotaz týká (potraviny, recepty, jídelníčky)
    """
    typ_otazky: Literal["potraviny", "recepty", "situace", "diety", "sestaveni_jidelnicku", "jine"] = Field(
        description="Urči, jaké oblasti výživy se dotaz týká")
    skore_jistoty: float = Field(
        description="Skóre jistoty mezi 0 a 1, 0 znamená, že si nejsi vůbec jistý svým rozhodnutím, 1 znamená, že si jsi úplně jistý svým rozhodnutím")
    duvod: str = Field(description="Důvod, podle kterého jsi se rozhodl")


def first_check(text: str):
    config = types.GenerateContentConfig(
        system_instruction="Tvým úkolem je určit, zda se tento text týká výživy. Uveď skóre jistoty a důvod.", response_mime_type="application/json", response_schema=PrvniUrceniVstupu
    )
    contents = types.Content(role="user", parts=[types.Part(text=text)])
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    formatted_res: PrvniUrceniVstupu = response.parsed
    return formatted_res


def check_question_sentence(text: str):
    config = types.GenerateContentConfig(
        system_instruction="""Tvým úkolem je určit, jestli je zadaný text otázka o jídle nebo oznámení o tom, co uživatel snědl. Vysvětlení kategorií:
        1. otazka - Zde by spadal text "Jaké výhody má losos?"
        2. oznameni - Zde by spadal text "Na oběd jsem snědl kuře s rýží."
        Uveď skóre jistoty a důvod, proč si do této kategorie zařadil daný dotaz
        """, response_mime_type="application/json", response_schema=UrceniVetaOtazka
    )
    contents = types.Content(role="user", parts=[types.Part(text=text)])
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    formatted_res: UrceniVetaOtazka = response.parsed
    return formatted_res


def type_check(text: str):
    config = types.GenerateContentConfig(
        system_instruction="""Tvým úkolem je určit, do které kategorie spadá následující dotaz. Vysvětlení kategorií:
        1. potraviny - Zde by spadala například otázka "Které potraviny mají vysoký obsah bílkovin?"
        2. recepty - Zde by spadala otázka "Vytvoř mi recept, který obsahuje kuřecí maso a má málo kalorií."
        3. situace - Zde by spadala otázka "Jak můžu jíst zdravě, když jsem na dovolené?"
        4. diety - Zde by spadala otázka "Pro koho je určená Paleo dieta?"
        5. sestaveni_jidelnicku - Zde by spadala otázka "Vytvoř mi jídelníček, mám rád ryby a chci zhubnout."
        6. jine - Do této kategorie zařaď všechny jiné otázky, které nemůžeš zařadit jinam, například "Co jsou to sacharidy?"
        Uveď skóre jistoty a důvod, proč si do této kategorie zařadil daný dotaz
        """, response_mime_type="application/json", response_schema=UrceniTypuOtazky
    )
    contents = types.Content(role="user", parts=[types.Part(text=text)])
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    structured_res: UrceniTypuOtazky = response.parsed
    return structured_res


def chatbot(query, profile):
    contents = []
    response1 = first_check(query)
    print(f"{response1.tyka_se_vyzivy}, skore: {response1.skore_jistoty}, duvod: {response1.duvod}")
    if not response1.tyka_se_vyzivy or response1.skore_jistoty < 0.7:
        return "Omlouvám se, ale na tento dotaz nemohu odpovědět, protože se specializuji pouze na výživu"
    response2 = check_question_sentence(query)
    print(f"{response2.typ_textu}, skore: {response2.skore_jistoty}, duvod: {response2.duvod}")
    if response2.skore_jistoty > 0.7 and response2.typ_textu == "oznameni":
        embedding_response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        try:
            embedding = embedding_response.embeddings[0].values
        except ValueError as e:
            return f"Chyba: {e}"
        info = search_potraviny(
            profile, embedding, update=True)
        contents = [types.Content(role="user", parts=[types.Part(text=json.dumps(info))]),
                    types.Content(role="user", parts=[types.Part(text=query)])
                    ]
        config = types.GenerateContentConfig(
            system_instruction="Text popisuje, co si uživatel dal na jídlo, tvým úkolem je rozebrat jednotlivé potraviny a napsat jejich výhody a nevýhody. Jako zdroj použij jen informace, které ti poskytnu. Na konec odpovědi napiš, že jsi jídlo zaznamenal do tabulky."
        )
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        return response.text
    response3 = type_check(query)
    print(f"{response3.typ_otazky}, skore: {response3.skore_jistoty}, duvod: {response3.duvod}")
    if response3.skore_jistoty < 0.7 or response3.typ_otazky == "jine":
        config = types.GenerateContentConfig(
            system_instruction="Jsi specialista na výživu. Odpověz na následující dotaz pouze pomocí přiloženého dokumentu. Pokud v dokumentu nenajdeš odpověď, napiš, že jsi v dokumentu nenašel odpověď na danou otázku"
        )
        contents = [types.Part.from_bytes(
            data=file.read_bytes(), mime_type="application/pdf"), query]
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        return response.text
    embedding_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    try:
        embedding = embedding_response.embeddings[0].values
    except ValueError as e:
        return f"Chyba: {e}"
    if response3.typ_otazky == "potraviny":
        return "Tuto možnost jsem ještě nenaprogramoval :/"
    elif response3.typ_otazky == "recepty":
        return "Tuto možnost jsem ještě nenaprogramoval :/"
    elif response3.typ_otazky == "situace":
        return "Tuto možnost jsem ještě nenaprogramoval :/"
    elif response3.typ_otazky == "diety":
        return "Tuto možnost jsem ještě nenaprogramoval :/"
    else:
        return "Tuto možnost jsem ještě nenaprogramoval :/"
