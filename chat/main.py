from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from .tools import tools

load_dotenv()

def chatbot(query):
    class ResearchResponse(BaseModel):
        summary: str


    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                Jsi fitness trenér, který se specializuje na výživu.
                Odpověz na dotaz uživatele a použij k tomu POUZE informace z přiloženého textu pomocí nástroje Najit_informace_z_textu, žádné jiné zdroje.
                **PRAVIDLA PRO SLOŽENÉ ÚKOLY:**
                -Pokud bude vstup obsahovat slovo "uložit" a název souboru, postupuj ve 2 krocích:
                1. Získej informace pomocí nástroje Najit_informace_z_textu.
                2. Ulož získaný text do souboru pomocí nástroje Ulozit_do_urceneho_souboru a jako filename použij název souboru ze vstupu.
                **PRAVIDLA PRO VÝSTUP:**
                -Pokud dotaz nesouvisí s tématem výživy, odpověz do pole "summary" hláškou: "Omlouvám se, na tuto otázku neumím odpovědět, protože se specializuji pouze na výživu.".
                -Pokud nástroj Najit_informace_z_textu vrátí prázdnou odpověď, napiš do pole "summary" hlášku: "Omlouvám se, na tuto otázku neumím pomocí přiloženého textu odpovědět.".
                -Ve všech ostatních případech napiš do pole "summary" odpověď z nástroje Najit_informace_z_textu.
                -Text rozděl do odstavců, aby byl lépe čitelný.
                -Výstup zabal do tohoto formátu a neuváděj žádný jiný text\n{format_instructions}.
                """,
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{query}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())


    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )

    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True)
    raw_response = agent_executor.invoke(
        {"query": query})

    try:
        output_string = raw_response.get(
            "output").strip('`json').strip('`').strip()
        structured_response = parser.parse(output_string)
        return f"{structured_response.summary}"
    except Exception as e:
        return f"Problém s parsováním odpovědi: {e}\nNeparsovaná odpověď:{raw_response}"
