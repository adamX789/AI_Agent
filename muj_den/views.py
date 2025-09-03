from django.shortcuts import render, redirect
from django.views.generic import View
from .models import Jidelnicek,VybraneRecepty
from .funkce import najdi_potravinu
from chat.models import Recepty

# Create your views here.


class MyDayView(View):
    def get(self,request):
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
            "denni_info":denni_info,
            "celkove_info":celkove_info,
            "potraviny":seznam_potravin,
            "jidelnicek":jidelnicek,
            "vybrane_recepty":vybrane_recepty
        }
        return render(request,"muj_den.html",context)
    
    def post(self,request):
        profile = request.user.profile
        print(request.POST)
        if "snedl_jsem" in request.POST:
            typ_jidla = request.POST.get("snedl_jsem")
            recept_id = int(request.POST.get("recept_id"))
            jidlo = Recepty.objects.get(id=recept_id)
            if typ_jidla == "snidane":
                profile.vybranerecepty.snidane = jidlo
                profile.vybranerecepty.snidane_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience,profile=profile)
            elif typ_jidla == "obed":
                profile.vybranerecepty.obed = jidlo
                profile.vybranerecepty.obed_snezen = True
                najdi_potravinu(ingredience=jidlo.ingredience,profile=profile)
            elif typ_jidla == "svacina1":
                profile.vybranerecepty.svacina1 = jidlo
                profile.vybranerecepty.svacina1_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience,profile=profile)
            elif typ_jidla == "svacina2":
                profile.vybranerecepty.svacina2 = jidlo
                profile.vybranerecepty.svacina2_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience,profile=profile)
            else:
                profile.vybranerecepty.vecere = jidlo
                profile.vybranerecepty.vecere_snezena = True
                najdi_potravinu(ingredience=jidlo.ingredience,profile=profile)
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
            "denni_info":denni_info,
            "celkove_info":celkove_info,
            "potraviny":seznam_potravin,
            "jidelnicek":jidelnicek,
            "vybrane_recepty":vybrane_recepty
        }
        return render(request,"muj_den.html",context)
