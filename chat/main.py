import pathlib
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import Literal
from .tools import *

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
    typ_textu: Literal["otazka", "oznameni_snedl", "oznameni_ma_chut"] = Field(
        description="Urči, jestli je text otázka o jídle, oznámení o tom, co uživatel snědl, nebo oznámení o tom, na co má uživatel chuť/co má v lednici")
    skore_jistoty: float = Field(
        description="Skóre jistoty mezi 0 a 1, 0 znamená, že si nejsi vůbec jistý svým rozhodnutím, 1 znamená, že si jsi úplně jistý svým rozhodnutím")
    duvod: str = Field(description="Důvod, podle kterého jsi se rozhodl")


class UrceniTypuOtazky(BaseModel):
    """
    Určí, jaké oblasti výživy se dotaz týká (potraviny, recepty, jídelníčky)
    """
    typ_otazky: Literal["potraviny", "recepty", "situace", "diety", "osobni_profil", "sestaveni_jidelnicku", "jine"] = Field(
        description="Urči, jaké oblasti výživy se dotaz týká")
    skore_jistoty: float = Field(
        description="Skóre jistoty mezi 0 a 1, 0 znamená, že si nejsi vůbec jistý svým rozhodnutím, 1 znamená, že si jsi úplně jistý svým rozhodnutím")
    duvod: str = Field(description="Důvod, podle kterého jsi se rozhodl")


class UrceniHmotnostiPotravin(BaseModel):
    potravina: str = Field(
        description="Název potraviny, například Losos, avokádo")
    hmotnost: float = Field(
        description="Hmotnost dané potraviny V GRAMECH NEBO MILILITRECH nebo MNOŽSTVI V KUSECH NEBO PLÁTKÁCH, uváděj jen číslo bez jednotky, tedy pro '200g' by mělo toto pole hodnotu 200, '150ml' by mělo hodnotu 150 a pro '1 kus' by mělo hodnotu 1.")
    jednotka:Literal["g","ml","ks","plátky"] = Field(description="Jednotka pro danou potravinu ('g' - gramy, 'ml' - mililitry, 'ks' - kusy, 'plátky' - plátky).")


class Jidla(BaseModel):
    seznam_jidla: list[UrceniHmotnostiPotravin] = Field(
        description="Seznam potraviny a její hmotnosti extrahované z textu")
    seznam_vsech_potravin: list[str] = Field(
        description="Seznam VŠECH potravin nalezených v textu")


class UrceniJidlaZObrazku(BaseModel):
    je_obrazek_jidla: bool = Field(
        description="Jestli je na obrázku jídlo v dostatečné kvalitě, aby šli určit potraviny.")
    potraviny: list[str] = Field(
        description="Z jakých potravin se jídlo skládá.")
    duvod: str = Field(description="Důvod pro tvé rozhodnutí.")


def first_check(text: str,historie:str):
    config = types.GenerateContentConfig(
        system_instruction=f"""Historie zpráv:
        {historie}
        Tvým úkolem je podle historie zpráv a aktuální zprávy určit, zda se tento text týká výživy. Uveď skóre jistoty a důvod.""", response_mime_type="application/json", response_schema=PrvniUrceniVstupu
    )
    contents = types.Content(role="user", parts=[types.Part(text=text)])
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    formatted_res: PrvniUrceniVstupu = response.parsed
    return formatted_res


def check_question_sentence(text: str,historie:str):
    config = types.GenerateContentConfig(
        system_instruction=f"""Historie zpráv:
        {historie}
        Tvým úkolem je podle historie zpráv a aktuální zprávy určit, jestli je zadaný text otázka o jídle nebo oznámení o tom, co uživatel snědl. Vysvětlení kategorií:
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


def get_weight_from_text(text: str):
    config = types.GenerateContentConfig(
        system_instruction="""Jsi expert na extrahování dat z textu. Tvým úkolem je z daného textu určit seznam VŠECH potravin a nápojů, a poté extrahovat názvy potravin nebo nápojů a jejich hmotnost v gramech nebo mililitrech NEBO počet kusů nebo plátků. Uveď jednotku (gramy, mililitry, kusy nebo plátky).
        **Pokud bude uvedene množství a název potraviny, ale bude chybět jednotka, nastav jednotku na kusy (ks)!**
        Pro zlomkové hodnoty (např. '1/2 jablka') vlož do pole hmotnost desetinnou hodnotu daného zlomku (např. 1/2 -> 0.5)
        Ignoruj gramatické chyby.""", response_mime_type="application/json", response_schema=Jidla
    )
    contents = types.Content(role="user", parts=[types.Part(text=text)])
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        structured_res: Jidla = response.parsed
        return structured_res
    except Exception as e:
        print(f"Chyba při extrakci dat: {e}")
        return Jidla(seznam_jidla=[],seznam_vsech_potravin=[])


def type_check(text: str,historie:str):
    config = types.GenerateContentConfig(
        system_instruction=f"""Historie zpráv:
        {historie}
        Tvým úkolem je podle historie zpráv a aktuální zprávy určit, do které kategorie spadá následující dotaz. Vysvětlení kategorií:
        1. potraviny - Zde spadají otázky, které se týkají informací nebo výpočtů pro konkrétní potraviny (např. "Jaké výhody má losos" nebo "Kolik gramů kuřecích prsou potřebuji, abych získal 20g tuků?")
        2. recepty - Zde spadají otázky, které se týkají informací nebo výpočtů pro konkrétní recepty (např. "Vytvoř mi recept, který obsahuje kuřecí maso a má málo kalorií." nebo "Kolik kalorií má vaječná omeleta se zeleninou?")
        3. situace - Zde by spadala otázka "Jak můžu jíst zdravě, když jsem na dovolené?"
        4. diety - Zde by spadala otázka "Pro koho je určená Paleo dieta?"
        5. osobni_profil - Zde by spadala otázka, která se týká tvého denního příjmu (např. "Kolik mi dnes ještě zbývá bílkovin?")
        6. sestaveni_jidelnicku - Zde by spadala otázka "Vytvoř mi jídelníček, mám rád ryby a chci zhubnout."
        7. jine - Do této kategorie zařaď všechny jiné otázky, které nemůžeš zařadit jinam, například "Co jsou to sacharidy?"
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


def chatbot(query, profile, last_agent_msg, denni_udaje, historie):
    profile_info = f"""
        Uživatel si nastavil tyto parametry:
        Denní příjem kalorií: {profile.denni_kalorie} kcal
        Denní příjem bílkovin: {profile.denni_bilkoviny} g
        Denní příjem sacharidů: {profile.denni_sacharidy} g
        Denní příjem tuků: {profile.denni_tuky} g
        Aktuální váha: {profile.aktualni_vaha} kg
        Cílová váha: {profile.cilova_vaha} kg
        Cíl: {profile.celkovy_cil}

        Dnešní celkový příjem uživatele:
        Kalorie: {denni_udaje.get("kalorie")}
        Bílkoviny: {denni_udaje.get("bilkoviny")}
        Sacharidy: {denni_udaje.get("sacharidy")}
        Tuky: {denni_udaje.get("tuky")}
    """
    contents = []
    historie_string = ""
    if historie:
        for message in historie:
            role = "user" if message.sender == "Vy" else "model"
            contents.append(types.Content(role=role, parts=[
                            types.Part(text=message.text)]))
            historie_string += f"{role}: {message.text}\n"

    response1 = first_check(query,historie_string)
    print(f"{response1.tyka_se_vyzivy}, skore: {response1.skore_jistoty}, duvod: {response1.duvod}")
    if not response1.tyka_se_vyzivy or response1.skore_jistoty < 0.7:
        return "Omlouvám se, ale na tento dotaz nemohu odpovědět, protože se specializuji pouze na výživu"
    response2 = check_question_sentence(query,historie_string)
    print(f"{response2.typ_textu}, skore: {response2.skore_jistoty}, duvod: {response2.duvod}")
    if response2.skore_jistoty > 0.7 and response2.typ_textu == "oznameni":
        new_query = query
        if last_agent_msg and "Z obrázku nalezeny potraviny" in last_agent_msg:
            foods = get_weight_from_text(query)
            potraviny_z_obrazku_text = last_agent_msg.split(
                ", prosím")[0].split("potraviny:")[1].strip()
            potraviny_z_obrazku = set(potravina.strip().lower(
            ) for potravina in potraviny_z_obrazku_text.split(","))
            print(potraviny_z_obrazku)
            potraviny_z_textu = set(potravina.lower()
                                    for potravina in foods.seznam_vsech_potravin)
            if not potraviny_z_obrazku == potraviny_z_textu:
                chybi_v_textu = potraviny_z_obrazku - potraviny_z_textu
                chybi_v_obrazku = potraviny_z_textu - potraviny_z_obrazku

                if chybi_v_textu:
                    return f"Pro některé potraviny/nápoje chybí hmotnost v gramech/mililitrech, prosím zadejte hmotnost potravin, abych je mohl zaznamenat do tabulky: {', '.join(chybi_v_textu)}"

                if chybi_v_obrazku:
                    return f"V obrázku nebyly nalezeny potraviny: {', '.join(chybi_v_obrazku)}!"
        elif last_agent_msg and "Pro některé potraviny/nápoje chybí hmotnost v gramech/mililitrech" in last_agent_msg:
            puvodni_text = historie.filter(
                sender="Vy").order_by("-id").first().text
            new_query = f"{puvodni_text}, {query}"
            foods = get_weight_from_text(new_query)
        else:
            foods = get_weight_from_text(query)
        if len(foods.seznam_vsech_potravin) != len(foods.seznam_jidla):
            return "Pro některé potraviny/nápoje chybí hmotnost v gramech/mililitrech, prosím zadejte hmotnost potravin, abych je mohl zaznamenat do tabulky."
        info = search_potraviny_and_update(profile, foods, client)
        contents.append(types.Content(role="user", parts=[
                        types.Part(text=json.dumps(info))]))
        contents.append(types.Content(
            role="user", parts=[types.Part(text=new_query)]))
        config = types.GenerateContentConfig(
            system_instruction="Text popisuje, co si uživatel dal na jídlo, tvým úkolem je rozebrat jednotlivé potraviny a napsat jejich výhody a nevýhody. Jako zdroj použij jen informace, které ti poskytnu. Na konec odpovědi napiš, že jsi jídlo zaznamenal do tabulky."
        )
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        return response.text
    response3 = type_check(query,historie_string)
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
        info = search_potraviny(embedding, pocet_vysledku=4)
    elif response3.typ_otazky == "recepty":
        info = search_recepty(embedding, pocet_vysledku=4)
    elif response3.typ_otazky == "situace":
        info = search_situace(embedding, pocet_vysledku=4)
    elif response3.typ_otazky == "diety":
        info = search_diety(embedding, pocet_vysledku=4)
    elif response3.typ_otazky == "osobni_profil":
        info = None
    else:
        return "Bohužel ještě neumím tvořit jídelníčky, ale mohu ti pomoct s trackováním potravin nebo zodpovězením otázek o výživě :)"
    if info:
        rag_string = f"V databázi jsem našel tyto informace pro zodpovězení otázky uživatele: {json.dumps(info)}"
        contents.append(types.Content(
            role="user", parts=[types.Part(text=rag_string)]))
    if response3.typ_otazky == "osobni_profil":
        contents.append(types.Content(role="user", parts=[
                        types.Part(text=profile_info)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=query)]))
    config = types.GenerateContentConfig(
        system_instruction="Jsi specialista na výživu a tvým úkolem je odpovědět na dotaz uživatele pouze pomocí přiložených informací. Vždy odpovídej přirozenou řečí."
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    return response.text


def chatbot_picture(image_bytes, mime_type):
    contents = types.Content(role="user", parts=[
                             types.Part.from_bytes(data=image_bytes, mime_type=mime_type)])
    config = types.GenerateContentConfig(system_instruction="Analyzuj následující obrázek. Pokud je na něm jídlo v takové kvalitě, že z něj jdou určit jednotlivé potraviny, urči názvy jednotlivých potravin (například kuřecí prso, brambory, mrkev) a seznam těchto potravin vlož do pole 'potraviny'. Pokud na obrázku vůbec jídlo není, a je tam např. pes nebo člověk, nevkládej do pole 'potraviny' nic.", response_schema=UrceniJidlaZObrazku, response_mime_type="application/json")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    formatted_response: UrceniJidlaZObrazku = response.parsed
    if not formatted_response.je_obrazek_jidla:
        return "Na tomto obrázku není jídlo, prosím vložte obrázek jídla."
    return f"Z obrázku nalezeny potraviny: {", ".join(formatted_response.potraviny)}, prosím zadejte množství těchto potravin."
