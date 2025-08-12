from dotenv import load_dotenv
from langchain_community.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool, StructuredTool
from datetime import datetime
import os
from django.conf import settings

load_dotenv()


def save_to_txt(data: str, filename: str = "vysledek.txt"):
    cas = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
    text = f"---Vysledek---\n{cas}\n\n{data}"
    with open(filename, "a", encoding="utf-8") as file:
        file.write(text)

    return f"Vysledek ulozen do souboru {filename}"


def save_to_named_file(data: str, filename: str):
    cas = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
    text = f"---Vysledek---\n{cas}\n\n{data}"
    with open(filename, "a", encoding="utf-8") as file:
        file.write(text)

    return f"Vysledek ulozen do souboru {filename}"


pdf_path = os.path.join(settings.BASE_DIR, "chat", "vyzivovy_specialista.pdf")
loader = PyPDFLoader(pdf_path)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

vector_store = Chroma.from_documents(
    documents=splits, embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"))

retriever = vector_store.as_retriever()
retriever_tool = create_retriever_tool(
    retriever=retriever,
    name="Najit_informace_z_textu",
    description="Najdi informace z přiloženého textu a odpověz na otázku."
)

save_tool = Tool(
    name="Ulozit_do_vychoziho_souboru",
    func=save_to_txt,
    description="Uloží veškeré informace do textového souboru s výchozím názvem 'vysledek.txt'.",
)

save_named_file = StructuredTool.from_function(
    name="Ulozit_do_urceneho_souboru",
    func=save_to_named_file,
    description="Uloží informace do textového souboru, jehož název je určen v inputu. Vstup musí obsahovat data a název souboru ve formátu 'filename=muj_soubor.txt'."
)

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name="DuckDuckGo_prohlizec",
    func=search.run,
    description="Prozkoumej web pro informace.",
)

wiki = WikipediaAPIWrapper(
    top_k_results=1, doc_content_chars_max=1000, wiki_client=any, lang="cs")
wiki_tool = WikipediaQueryRun(api_wrapper=wiki, name="Wikipedie")

tools = [retriever_tool, save_named_file, save_tool]
