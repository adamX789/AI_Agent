from django.shortcuts import render, redirect
from django.views.generic import View
from .models import Jidelnicek, VybraneRecepty
from .funkce import najdi_potravinu, call_llm
from chat.models import Recepty, Potraviny, Makroziviny
from decimal import Decimal
from django.contrib import messages
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
# Create your views here.

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


class MyDayView(View):
    def get(self, request):
        profile = request.user.profile
        jidelnicek = Jidelnicek.objects.get(profile=profile)
        vybrane_recepty = VybraneRecepty.objects.get(profile=profile)
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            jednotka = food_item.jednotka
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id": food_item.id,
                "hmotnost": hmotnost,
                "jednotka": jednotka,
                "kalorie": makroziviny.kalorie*multiplier,
                "bilkoviny": makroziviny.bilkoviny_gramy*multiplier,
                "sacharidy": makroziviny.sacharidy_gramy*multiplier,
                "tuky": makroziviny.tuky_gramy*multiplier,
            })
            celkove_kalorie += makroziviny.kalorie*multiplier
            celkove_bilkoviny += makroziviny.bilkoviny_gramy*multiplier
            celkove_sacharidy += makroziviny.sacharidy_gramy*multiplier
            celkove_tuky += makroziviny.tuky_gramy*multiplier

        denni_info = {
            "denni_k": denni_kalorie if denni_kalorie else 0,
            "denni_b": denni_bilkoviny if denni_bilkoviny else 0,
            "denni_s": denni_sacharidy if denni_sacharidy else 0,
            "denni_t": denni_tuky if denni_tuky else 0,
            "pitny_rezim": pitny_rezim if pitny_rezim else 0,
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
        }
        context = {
            "denni_info": denni_info,
            "celkove_info": celkove_info,
            "potraviny": seznam_potravin,
            "jidelnicek": jidelnicek,
            "vybrane_recepty": vybrane_recepty
        }
        return render(request, "muj_den.html", context)

    def post(self, request):
        profile = request.user.profile
        print(request.POST)
        if "snedl_jsem" in request.POST:
            typ_jidla = request.POST.get("snedl_jsem")
            recept_id = int(request.POST.get("recept_id"))
            jidlo = Recepty.objects.get(id=recept_id)
            if typ_jidla == "snidane":
                profile.vybranerecepty.snidane = jidlo
                profile.vybranerecepty.snidane_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience, profile=profile)
            elif typ_jidla == "obed":
                profile.vybranerecepty.obed = jidlo
                profile.vybranerecepty.obed_snezen = True
                najdi_potravinu(ingredience=jidlo.ingredience, profile=profile)
            elif typ_jidla == "svacina1":
                profile.vybranerecepty.svacina1 = jidlo
                profile.vybranerecepty.svacina1_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience, profile=profile)
            elif typ_jidla == "svacina2":
                profile.vybranerecepty.svacina2 = jidlo
                profile.vybranerecepty.svacina2_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience, profile=profile)
            else:
                profile.vybranerecepty.vecere = jidlo
                profile.vybranerecepty.vecere_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience, profile=profile)
            profile.vybranerecepty.save()
            profile.save()
        jidelnicek = Jidelnicek.objects.get(profile=profile)
        vybrane_recepty = VybraneRecepty.objects.get(profile=profile)
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            if request.POST.get("delete") == "del" + str(food_item.id):
                profile.food_set.filter(id=food_item.id).delete()
                continue
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            jednotka = food_item.jednotka
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id": food_item.id,
                "hmotnost": hmotnost,
                "jednotka": jednotka,
                "kalorie": makroziviny.kalorie*multiplier,
                "bilkoviny": makroziviny.bilkoviny_gramy*multiplier,
                "sacharidy": makroziviny.sacharidy_gramy*multiplier,
                "tuky": makroziviny.tuky_gramy*multiplier,
            })
            celkove_kalorie += makroziviny.kalorie*multiplier
            celkove_bilkoviny += makroziviny.bilkoviny_gramy*multiplier
            celkove_sacharidy += makroziviny.sacharidy_gramy*multiplier
            celkove_tuky += makroziviny.tuky_gramy*multiplier

        denni_info = {
            "denni_k": denni_kalorie if denni_kalorie else 0,
            "denni_b": denni_bilkoviny if denni_bilkoviny else 0,
            "denni_s": denni_sacharidy if denni_sacharidy else 0,
            "denni_t": denni_tuky if denni_tuky else 0,
            "pitny_rezim": pitny_rezim if pitny_rezim else 0,
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
        }
        context = {
            "denni_info": denni_info,
            "celkove_info": celkove_info,
            "potraviny": seznam_potravin,
            "jidelnicek": jidelnicek,
            "vybrane_recepty": vybrane_recepty
        }
        return render(request, "muj_den.html", context)


class AddView(View):
    def get(self, request):
        profile = request.user.profile
        seznam_potravin = Potraviny.objects.all().values_list("nazev", flat=True)
        return render(request, "add.html", {"potraviny": list(seznam_potravin)})

    def post(self, request):
        profile = request.user.profile
        print(request.POST)
        if request.POST.get("add") == "a":
            potravina_nazev = request.POST.get("potravina")
            potravina = Potraviny.objects.get(nazev=potravina_nazev)
            mnozstvi = Decimal(request.POST.get("mnozstvi"))
            jednotka = request.POST.get("jednotka")
            if jednotka in ["g", "ml"]:
                profile.food_set.create(
                    potravina=potravina, jednotka=jednotka, hmotnost_g=mnozstvi)
            else:
                odpoved = call_llm(
                    potravina=potravina_nazev, jednotka=jednotka)
                profile.food_set.create(
                    potravina=potravina, jednotka="g", hmotnost_g=mnozstvi*Decimal(odpoved))
            profile.save()
        return redirect("my_day")


class AddFoodView(View):
    def get(self, request):
        return render(request, "addfood.html", {})

    def post(self, request):
        if request.POST.get("pridat"):
            print(request.POST)
            nazev = request.POST.get("name")
            if not nazev:
                messages.error(request, "Prosím zadejte název potraviny.")
                return render(request, "addfood.html", {})
            if Potraviny.objects.filter(nazev=nazev).exists():
                messages.error(request, "Tato potravina už existuje!")
                return render(request, "addfood.html", {})
            popis = request.POST.get("desc")
            kalorie = int(request.POST.get("kcal"))
            bilkoviny = Decimal(request.POST.get("protein"))
            tuky = Decimal(request.POST.get("fat"))
            sacharidy = Decimal(request.POST.get("carbs"))
            if Decimal(kalorie) - (4*bilkoviny + 4*sacharidy + 9*tuky) > Decimal(5) or Decimal(kalorie) - (4*bilkoviny + 4*sacharidy + 9*tuky) < Decimal(-5):
                messages.error(
                    request, "Zadané makroživiny neodpovídají celkovým kaloriím potraviny!")
                return render(request, "addfood.html", {})
            benefity_str = request.POST.get("benefits")
            vhodne_pro_str = request.POST.get("best_for")
            nekonzumujte_pokud_str = request.POST.get("avoid_if")
            benefity = [item.strip() for item in benefity_str.split(",")]
            vhodne_pro = [item.strip() for item in vhodne_pro_str.split(",")]
            nekonzumujte_pokud = [item.strip()
                                  for item in nekonzumujte_pokud_str.split(",")]
            embedding_text = f"""
            Název: {nazev}
            Popis: {popis}
            Výhody: {", ".join(benefity)}
            Nejlepší pro: {", ".join(vhodne_pro)}
            Nekonzumujte pokud: {", ".join(nekonzumujte_pokud)}
            """
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=embedding_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            embedding = response.embeddings[0].values
            potravina = Potraviny.objects.create(
                nazev=nazev,
                popis=popis,
                vyhody=benefity,
                nejlepsi_pro=vhodne_pro,
                nekonzumujte_pokud=nekonzumujte_pokud,
                embedding=embedding
            )
            Makroziviny.objects.create(
                potravina=potravina,
                kalorie=kalorie,
                bilkoviny_gramy=bilkoviny,
                sacharidy_gramy=sacharidy,
                tuky_gramy=tuky
            )
        return redirect("my_day")
