import pathlib
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()

def chatbot(query):
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    file = pathlib.Path("chat/vyzivovy_specialista.pdf")
    instrukce = "Odpověz na následující dotaz pouze pomocí přiloženého dokumentu. Pokud v dokumentu nenajdeš odpověď, napiš, že jsi v dokumentu nenašel odpověď na danou otázku"
    dotaz = f"{instrukce}\n\n{query}"
    contents = [types.Part.from_bytes(data=file.read_bytes(),mime_type="application/pdf"), dotaz]
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
    )
    return response.text




    
