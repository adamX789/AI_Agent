from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from chat.models import Makroziviny
from django.contrib import messages
from .funkce import *
from decimal import Decimal

# Create your views here.


class ProfileView(View):
    def get(self, request):
        profile = request.user.profile
        jmeno = profile.jmeno if profile.jmeno else ""
        vek = profile.vek if profile.vek else 0
        aktivita = profile.aktivita if profile.aktivita else ""
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id": food_item.id,
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
            "pitny_rezim": pitny_rezim if pitny_rezim else 0,
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
            "akt_vaha": profile.aktualni_vaha if profile.aktualni_vaha else 0,
            "cil_vaha": profile.cilova_vaha if profile.cilova_vaha else 0,
            "cil": profile.celkovy_cil if profile.celkovy_cil else ""
        }
        context = {
            "username": jmeno,
            "vek": vek,
            "aktivita": aktivita,
            "denni_info": denni_info,
            "celkove_info": celkove_info,
            "potraviny": seznam_potravin
        }
        return render(request, "profil.html", context)

    def post(self, request):
        profile = request.user.profile
        jmeno = profile.jmeno if profile.jmeno else ""
        vek = profile.vek if profile.vek else 0
        aktivita = profile.aktivita if profile.aktivita else ""
        for item in profile.food_set.all():
            if request.POST.get("del" + str(item.id)) == "c":
                profile.food_set.get(id=item.id).delete()
                profile.save()
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim = (
            profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry)
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            multiplier = hmotnost / 100
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "id": food_item.id,
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
            "pitny_rezim": pitny_rezim if pitny_rezim else 0,
        }
        celkove_info = {
            "celkove_k": celkove_kalorie,
            "celkove_b": celkove_bilkoviny,
            "celkove_s": celkove_sacharidy,
            "celkove_t": celkove_tuky,
            "akt_vaha": profile.aktualni_vaha if profile.aktualni_vaha else 0,
            "cil_vaha": profile.cilova_vaha if profile.cilova_vaha else 0,
            "cil": profile.celkovy_cil if profile.celkovy_cil else ""
        }
        context = {
            "username": jmeno,
            "vek": vek,
            "aktivita": aktivita,
            "denni_info": denni_info,
            "celkove_info": celkove_info,
            "potraviny": seznam_potravin
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
            profile.jmeno = request.POST.get("jmeno")
            profile.pohlavi = request.POST.get("pohlavi")
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


class StartFormView(View):
    def get(self, request):
        return render(request, "form.html", {})

    def post(self, request):
        profile = request.user.profile
        profile.jmeno = request.POST.get("jmeno")
        profile.vek = int(request.POST.get("vek"))
        pohlavi = request.POST.get("pohlavi")
        if pohlavi == "muz":
            profile.pohlavi = "Muž"
        elif pohlavi == "zena":
            profile.pohlavi = "Žena"
        elif pohlavi == "jine":
            profile.pohlavi = "Jiné"
        else:
            messages.error(request, "Prosím vyberte pohlaví.")
            return render(request, "form.html", {})
        profile.vyska_v_cm = Decimal(request.POST.get("vyska"))
        profile.aktualni_vaha = Decimal(request.POST.get("vaha"))
        profile.cilova_vaha = Decimal(request.POST.get("cilova_vaha"))
        cil = request.POST.get("cil")
        if cil == "n":
            profile.celkovy_cil = "Nabrat svaly"
        elif cil == "u":
            profile.celkovy_cil = "Udržet váhu"
        elif cil == "z":
            profile.celkovy_cil = "Zhubnout"
        else:
            messages.error(request, "Prosím vyberte cíl.")
            return render(request, "form.html", {})
        aktivita = request.POST.get("aktivita")
        if aktivita == "sedavy":
            profile.aktivita = "Sedavý"
        if aktivita == "lehka":
            profile.aktivita = "Lehká aktivita"
        elif aktivita == "stredni":
            profile.aktivita = "Střední aktivita"
        elif aktivita == "vysoka":
            profile.aktivita = "Vysoká aktivita"
        elif aktivita == "extremni":
            profile.aktivita = "Extrémně vysoká aktivita"
        else:
            messages.error(request, "Prosím vyberte aktivitu.")
            return render(request, "form.html", {})
        omezeni = request.POST.get("omezeni")
        if omezeni == "alergie":
            profile.zdravotni_omezeni = "Alergie"
        elif omezeni == "cukrovka":
            profile.zdravotni_omezeni = "Cukrovka"
        elif omezeni == "srdecni":
            profile.zdravotni_omezeni = "Srdeční problémy"
        elif omezeni == "jine":
            profile.zdravotni_omezeni = "Jiné"
        else:
            profile.zdravotni_omezeni = ""
        dieta = request.POST.get("dieta")
        if dieta == "vegan":
            profile.dieta = "Veganská"
        elif dieta == "vegetarian":
            profile.dieta = "Vegetariánská"
        if dieta == "keto":
            profile.dieta = "Keto"
        if dieta == "paleo":
            profile.dieta = "Paleo"
        else:
            profile.dieta = ""
        profile.save()
        if profile.celkovy_cil == "Udržet váhu":
            if profile.jednoduchy_formular:
                bmr = get_bmr_simple(pohlavi=profile.pohlavi, vek=profile.vek,
                                     vyska=profile.vyska_v_cm, vaha=profile.aktualni_vaha)
                profile.denni_kalorie = get_tdee(
                    bmr=bmr, vek=profile.vek, aktivita=profile.aktivita)
                profile.save()
                profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_simple(
                    cals=profile.denni_kalorie, vaha=profile.aktualni_vaha)
            else:
                bmr = 0
                profile.denni_kalorie = get_tdee(
                    bmr=bmr, vek=profile.vek, aktivita=profile.aktivita)
                profile.save()
            profile.save()
            return redirect("profile")
        else:
            print(profile.aktualni_vaha)
            return redirect("info")


class ChoiceView(View):
    def get(self, request):
        return render(request, "choice.html", {})

    def post(self, request):
        profile = request.user.profile
        if request.POST.get("start") == "detailed":
            profile.jednoduchy_formular = False
        else:
            profile.jednoduchy_formular = True
        profile.save()
        return redirect("form")


class InfoView(View):
    def get(self, request):
        profile = request.user.profile
        if profile.celkovy_cil == "Zhubnout":
            return render(request, "hubnuti.html", {})
        return render(request, "nabirani.html", {})

    def post(self, request):
        profile = request.user.profile
        if profile.jednoduchy_formular:
            bmr = get_bmr_simple(pohlavi=profile.pohlavi, vek=profile.vek,
                                 vyska=profile.vyska_v_cm, vaha=profile.aktualni_vaha)
        else:
            bmr = 0
        tdee = get_tdee(bmr=bmr, vek=profile.vek, aktivita=profile.aktivita)
        if profile.celkovy_cil == "Zhubnout":
            choice = request.POST.get("cutting")
            if choice == "extreme":
                x = 1
            elif choice == "fast-sustainable":
                x = 0.75
            elif choice == "medium":
                x = 0.5
            else:
                x = 0.25
            profile.denni_kalorie = get_cals_cut(tdee=tdee, bmr=bmr, x=x)
            profile.save()
        else:
            yes_count = 0
            for i in range(1, 4):
                if request.POST.get("q" + str(i)) == "yes":
                    yes_count += 1
            profile.denni_kalorie = get_cals_bulk(
                tdee=tdee, yes_count=yes_count)
            profile.save()

        profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_simple(
            cals=profile.denni_kalorie, vaha=profile.aktualni_vaha)
        profile.save()
        return redirect("profile")
