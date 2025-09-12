from django.shortcuts import render, redirect
from django.views.generic import View
from .models import Jidelnicek
from .funkce import najdi_potravinu, call_llm
from chat.models import Recepty, Potraviny, Makroziviny,Aktivita
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
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        seznam_aktivit = []
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
        for aktivita in profile.activity_set.all():
            aktivita_obj = aktivita.aktivita
            spalene_kalorie = aktivita_obj.met_hodnota*profile.aktualni_vaha*Decimal(aktivita.cas_min/60)
            seznam_aktivit.append({
                "nazev": aktivita_obj.typ_aktivity,
                "id": aktivita.id,
                "cas": aktivita.cas_min,
                "spalene_kalorie":round(spalene_kalorie,1)
            })
            celkove_kalorie -= spalene_kalorie
        seznam_snidani = []
        seznam_svacin1 = []
        seznam_obedu = []
        seznam_svacin2 = []
        seznam_veceri = []
        for recept in jidelnicek.jidelnicekrecept_set.all():
            seznam_ingredienci = []
            for ingredience in recept.recept.ingredience:
                nazev = ingredience["nazev"]
                hodnota_str = ingredience["mnozstvi"].strip().split(" ")[0]
                try:
                    hodnota = float(hodnota_str)
                except ValueError:
                    numerator, denominator = map(float, hodnota_str.split('/'))
                    hodnota = numerator / denominator
                nova_hodnota = Decimal(hodnota)*recept.scale_factor
                jednotka = ingredience["mnozstvi"].strip().split(" ")[1]
                seznam_ingredienci.append({
                    "nazev":nazev,
                    "mnozstvi":nova_hodnota,
                    "jednotka":jednotka
                })
            if recept.chod == "snidane":
                seznam_snidani.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod == "svacina1":
                seznam_svacin1.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod =="obed":
                seznam_obedu.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod == "svacina2":
                seznam_svacin2.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            else:
                seznam_veceri.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
        jidelnicek = {
            "snidane":seznam_snidani,
            "snidane_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="snidane", snezeno=True).exists(),
            "svacina1":seznam_svacin1,
            "svacina1_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="svacina1", snezeno=True).exists(),
            "obed":seznam_obedu,
            "obed_snezen":jidelnicek.jidelnicekrecept_set.filter(chod="obed", snezeno=True).exists(),
            "svacina2":seznam_svacin2,
            "svacina2_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="svacina2", snezeno=True).exists(),
            "vecere":seznam_veceri,
            "vecere_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="vecere", snezeno=True).exists(),
        }
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
            "aktivity":seznam_aktivit,
            "jidelnicek": jidelnicek,
        }
        return render(request, "muj_den.html", context)

    def post(self, request):
        profile = request.user.profile
        jidelnicek = Jidelnicek.objects.get(profile=profile)
        print(request.POST)
        if "snedl_jsem" in request.POST:
            recept_id = int(request.POST.get("recept_id"))
            ingredience_list = []
            jidlo = Recepty.objects.get(id=recept_id)
            jidlo_v_jidelnicku = jidelnicek.jidelnicekrecept_set.get(recept=jidlo)
            jidlo_v_jidelnicku.snezeno = True
            jidlo_v_jidelnicku.save()
            for ingredience in jidlo.ingredience:
                hodnota_str = ingredience["mnozstvi"].strip().split(" ")[0]
                try:
                    hodnota = float(hodnota_str)
                except ValueError:
                    numerator, denominator = map(float, hodnota_str.split('/'))
                    hodnota = numerator / denominator
                nova_hodnota = float(Decimal(hodnota)*jidlo_v_jidelnicku.scale_factor)
                jednotka = ingredience["mnozstvi"].strip().split(" ")[1]
                ingredience_list.append({
                    "nazev":ingredience["nazev"],
                    "mnozstvi": f"{nova_hodnota} {jednotka}"
                })
            najdi_potravinu(ingredience=ingredience_list, profile=profile)
            profile.save()
            jidelnicek.save()
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        seznam_aktivit = []
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
        for aktivita in profile.activity_set.all():
            aktivita_obj = aktivita.aktivita
            spalene_kalorie = aktivita_obj.met_hodnota*profile.aktualni_vaha*Decimal(aktivita.cas_min/60)
            seznam_aktivit.append({
                "nazev": aktivita_obj.typ_aktivity,
                "id": aktivita.id,
                "cas": aktivita.cas_min,
                "spalene_kalorie":round(spalene_kalorie,1)
            })
            celkove_kalorie -= spalene_kalorie
        seznam_snidani = []
        seznam_svacin1 = []
        seznam_obedu = []
        seznam_svacin2 = []
        seznam_veceri = []
        for recept in jidelnicek.jidelnicekrecept_set.all():
            seznam_ingredienci = []
            for ingredience in recept.recept.ingredience:
                nazev = ingredience["nazev"]
                hodnota_str = ingredience["mnozstvi"].strip().split(" ")[0]
                try:
                    hodnota = float(hodnota_str)
                except ValueError:
                    numerator, denominator = map(float, hodnota_str.split('/'))
                    hodnota = numerator / denominator
                nova_hodnota = Decimal(hodnota)*recept.scale_factor
                jednotka = ingredience["mnozstvi"].strip().split(" ")[1]
                seznam_ingredienci.append({
                    "nazev":nazev,
                    "mnozstvi":nova_hodnota,
                    "jednotka":jednotka
                })
            if recept.chod == "snidane":
                seznam_snidani.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod == "svacina1":
                seznam_svacin1.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod =="obed":
                seznam_obedu.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            elif recept.chod == "svacina2":
                seznam_svacin2.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
            else:
                seznam_veceri.append({
                    "id":recept.recept.id,
                    "nazev_receptu":recept.recept.nazev,
                    "ingredience":seznam_ingredienci,
                })
        jidelnicek = {
            "snidane":seznam_snidani,
            "snidane_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="snidane", snezeno=True).exists(),
            "svacina1":seznam_svacin1,
            "svacina1_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="svacina1", snezeno=True).exists(),
            "obed":seznam_obedu,
            "obed_snezen":jidelnicek.jidelnicekrecept_set.filter(chod="obed", snezeno=True).exists(),
            "svacina2":seznam_svacin2,
            "svacina2_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="svacina2", snezeno=True).exists(),
            "vecere":seznam_veceri,
            "vecere_snezena":jidelnicek.jidelnicekrecept_set.filter(chod="vecere", snezeno=True).exists(),
        }
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
            "aktivity":seznam_aktivit,
            "jidelnicek": jidelnicek,
        }
        return render(request, "muj_den.html", context)


class AddView(View):
    def get(self, request):
        profile = request.user.profile
        seznam_potravin = Potraviny.objects.all().values_list("nazev", flat=True)
        seznam_aktivit = Aktivita.objects.all().values_list("typ_aktivity",flat=True)
        return render(request, "add.html", {"potraviny": list(seznam_potravin), "aktivity": list(seznam_aktivit)})

    def post(self, request):
        profile = request.user.profile
        print(request.POST)
        if request.POST.get("add") == "a":
            objekt = request.POST.get("objekt")
            jednotka = request.POST.get("jednotka")
            if jednotka == "min":
                mnozstvi = int(request.POST.get("mnozstvi"))
                aktivita = Aktivita.objects.get(typ_aktivity=objekt)
                profile.activity_set.create(aktivita=aktivita, cas_min=mnozstvi)
            else:
                mnozstvi = Decimal(request.POST.get("mnozstvi"))
                potravina = Potraviny.objects.get(nazev=objekt)
                if jednotka in ["g", "ml"]:
                    profile.food_set.create(
                        potravina=potravina, jednotka=jednotka, hmotnost_g=mnozstvi)
                else:
                    odpoved = call_llm(
                        potravina=objekt, jednotka=jednotka)
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
            if Decimal(kalorie) - (4*bilkoviny + 4*sacharidy + 9*tuky) > Decimal(20) or Decimal(kalorie) - (4*bilkoviny + 4*sacharidy + 9*tuky) < Decimal(-20):
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
