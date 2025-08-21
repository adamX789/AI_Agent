from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from chat.models import Makroziviny
from django.contrib import messages

# Create your views here.


class ProfileView(View):
    def get(self, request):
        profile = request.user.profile
        username = request.user.username
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id":food_item.id,
                "hmotnost": hmotnost,
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
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
            "akt_vaha":profile.aktualni_vaha if profile.aktualni_vaha else 0,
            "cil_vaha":profile.cilova_vaha if profile.cilova_vaha else 0,
            "cil":profile.celkovy_cil if profile.celkovy_cil else ""
        }
        context = {
            "username":username,
            "denni_info":denni_info,
            "celkove_info":celkove_info,
            "potraviny":seznam_potravin
        }
        return render(request, "profil.html", context)

    def post(self, request):
        profile = request.user.profile
        username = request.user.username
        for item in profile.food_set.all():
            if request.POST.get("del" + str(item.id)) == "c":
                profile.food_set.get(id=item.id).delete()
                profile.save()
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id":food_item.id,
                "hmotnost": hmotnost,
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
            "denni_k": denni_kalorie,
            "denni_b": denni_bilkoviny,
            "denni_s": denni_sacharidy,
            "denni_t": denni_tuky,
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
            "akt_vaha":profile.aktualni_vaha,
            "cil_vaha":profile.cilova_vaha,
            "cil":profile.celkovy_cil
        }
        context = {
            "username":username,
            "denni_info":denni_info,
            "celkove_info":celkove_info,
            "potraviny":seznam_potravin
        }
        return render(request, "profil.html", context)


class EditView(View):
    def get(self, request):
        profile = request.user.profile
        udaje = {
            "kalorie": profile.denni_kalorie,
            "bilkoviny": profile.denni_bilkoviny,
            "sacharidy": profile.denni_sacharidy,
            "tuky": profile.denni_tuky,
            "vaha_akt": profile.aktualni_vaha,
            "vaha_cil": profile.cilova_vaha,
            "cil": profile.celkovy_cil
        }
        return render(request, "edit.html", udaje)

    def post(self, request):
        if request.POST.get("ulozit"):
            profile = request.user.profile
            profile.denni_kalorie = request.POST.get("kalorie")
            profile.denni_bilkoviny = request.POST.get("bilkoviny")
            profile.denni_sacharidy = request.POST.get("sacharidy")
            profile.denni_tuky = request.POST.get("tuky")
            profile.aktualni_vaha = request.POST.get("vaha_akt")
            profile.cilova_vaha = request.POST.get("vaha_cil")
            cil = request.POST.get("cil")
            if cil == "z":
                profile.celkovy_cil = "Zhubnout"
            elif cil == "n":
                profile.celkovy_cil = "Nabrat"
            elif cil == "u":
                profile.celkovy_cil = "Udržet váhu"
            profile.save()
        return redirect("profile")
        
