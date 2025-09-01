from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from chat.models import Makroziviny
from django.contrib import messages
from .funkce import *
from muj_den.funkce import sestav_jidelnicek
from decimal import Decimal

# Create your views here.


class ProfileView(View):
    def get(self, request):
        profile = request.user.profile
        jmeno = profile.jmeno if profile.jmeno else ""
        pohlavi = profile.pohlavi if profile.pohlavi else ""
        vek = profile.vek if profile.vek else 0
        vyska = profile.vyska_v_cm if profile.vyska_v_cm else 0
        aktivita = profile.aktivita if profile.aktivita else ""
        aktualni_vaha = profile.aktualni_vaha if profile.aktualni_vaha else 0
        cilova_vaha = profile.cilova_vaha if profile.cilova_vaha else 0
        cil = profile.celkovy_cil if profile.celkovy_cil else ""
        zdravotni_omezeni = profile.zdravotni_omezeni if profile.zdravotni_omezeni else ""
        dieta = profile.dieta if profile.dieta else ""

        context = {
            "jmeno": jmeno,
            "vek": vek,
            "pohlavi": pohlavi,
            "vyska": vyska,
            "aktivita": aktivita,
            "akt_vaha": aktualni_vaha,
            "cil_vaha": cilova_vaha,
            "cil": cil,
            "zdravotni_omezeni": zdravotni_omezeni,
            "dieta": dieta
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
            "jmeno": profile.jmeno,
            "vek": profile.vek,
            "vyska": profile.vyska_v_cm,
            "vaha_akt": profile.aktualni_vaha,
            "pohlavi": profile.pohlavi,
            "aktivita": profile.aktivita,
            "zdravotni_omezeni": profile.zdravotni_omezeni,
            "dieta": profile.dieta,
            "vaha_cil": profile.cilova_vaha,
            "cil": profile.celkovy_cil
        }
        return render(request, "edit.html", udaje)

    def post(self, request):
        profile = request.user.profile
        profile.jmeno = request.POST.get("jmeno")
        profile.vek = request.POST.get("vek")
        profile.vyska_v_cm = Decimal(request.POST.get("vyska"))
        profile.aktualni_vaha = Decimal(request.POST.get("vaha_akt"))
        pohlavi = request.POST.get("pohlavi")
        profile.pohlavi = "Muž" if pohlavi == "muz" else (
            "Žena" if pohlavi == "zena" else "Jiné")
        aktivita = request.POST.get("aktivita")
        if aktivita == "sedavy":
            profile.aktivita = "Sedavý"
        if aktivita == "lehka":
            profile.aktivita = "Lehká aktivita"
        elif aktivita == "stredni":
            profile.aktivita = "Střední aktivita"
        elif aktivita == "vysoka":
            profile.aktivita = "Vysoká aktivita"
        else:
            profile.aktivita = "Extrémně vysoká aktivita"

        omezeni = request.POST.get("zdravotni")
        if omezeni == "alergie":
            profile.zdravotni_omezeni = "Alergie"
        elif omezeni == "cukrovka":
            profile.zdravotni_omezeni = "Cukrovka"
        elif omezeni == "srdecni":
            profile.zdravotni_omezeni = "Srdeční problémy"
        elif omezeni == "jine":
            profile.zdravotni_omezeni = "Jiné"
        else:
            profile.zdravotni_omezeni = "Nemám"

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
            profile.dieta = "Žádná"

        profile.cilova_vaha = Decimal(request.POST.get("vaha_cil"))
        cil = request.POST.get("cil")
        if cil == "z":
            profile.celkovy_cil = "Zhubnout"
        elif cil == "n":
            profile.celkovy_cil = "Nabrat svaly"
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
            profile.zdravotni_omezeni = "Nemám"
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
            profile.dieta = "Žádná"
        profile.save()
        if profile.celkovy_cil == "Udržet váhu":
            if profile.jednoduchy_formular:
                bmr = get_bmr_simple(pohlavi=profile.pohlavi, vek=profile.vek,
                                     vyska=profile.vyska_v_cm, vaha=profile.aktualni_vaha)
                profile.denni_kalorie = int(round(get_tdee(
                    bmr=bmr, vek=profile.vek, aktivita=profile.aktivita), 0))
                profile.save()
                profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_simple(
                    cals=profile.denni_kalorie, vaha=profile.aktualni_vaha)
                profile.save()
                sestav_jidelnicek(profile=profile)
                return redirect("profile")
            else:
                return redirect("bodyfat")
        else:
            if profile.jednoduchy_formular:
                return redirect("info")
            else:
                return redirect("bodyfat")


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
            lbm = get_lbm(vaha=profile.aktualni_vaha,
                          bodyfat=profile.procento_telesneho_tuku)
            bmr = get_bmr_advanced(lbm=lbm)
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
            profile.denni_kalorie = int(
                round(get_cals_cut(tdee=tdee, bmr=bmr, x=x), 0))
        else:
            yes_count = 0
            for i in range(1, 4):
                if request.POST.get("q" + str(i)) == "yes":
                    yes_count += 1
            profile.denni_kalorie = int(round(get_cals_bulk(
                tdee=tdee, yes_count=yes_count), 0))
        profile.save()

        if profile.jednoduchy_formular:
            profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_simple(
                cals=profile.denni_kalorie, vaha=profile.aktualni_vaha)
        else:
            profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_advanced(
                cals=profile.denni_kalorie, lbm=lbm, vaha=profile.aktualni_vaha, aktivita=profile.aktivita, vek=profile.vek)
        profile.save()
        sestav_jidelnicek(profile=profile)
        return redirect("profile")


class BodyFatView(View):
    def get(self, request):
        profile = request.user.profile
        return render(request, "bodyfat.html", {"pohlavi": profile.pohlavi})

    def post(self, request):
        profile = request.user.profile
        if request.FILES:
            image_file = request.FILES["image"]
            image_bytes = image_file.read()
            mime_type = image_file.content_type
            bodyfat = get_bf_by_image(
                image_bytes=image_bytes, mime_type=mime_type)
            if bodyfat <= Decimal("0"):
                messages.error(
                    request, "Ze vloženého obrázku nelze určit procento tělesného tuku! Prosím vložte platný obrázek.")
                return render(request, "bodyfat.html", {"pohlavi": profile.pohlavi, "volba": "obrazek"})
        else:
            profile.obvod_pasu_cm = Decimal(request.POST.get("pas"))
            profile.obvod_krku_cm = Decimal(request.POST.get("krk"))
            profile.obvod_boku_cm = Decimal(request.POST.get(
                "boky")) if request.POST.get("boky") else 0

            profile.save()
            bodyfat = get_bf_by_measures(pohlavi=profile.pohlavi, pas=profile.obvod_pasu_cm,
                                         krk=profile.obvod_krku_cm, boky=profile.obvod_boku_cm, vyska=profile.vyska_v_cm)
            if bodyfat <= Decimal("0"):
                messages.error(request, "Prosím zadejte realistické obvody.")
                return render(request, "bodyfat.html", {"pohlavi": profile.pohlavi, "volba": "rozmery"})
        profile.procento_telesneho_tuku = bodyfat
        profile.save()

        if profile.celkovy_cil == "Udržet váhu":
            lbm = get_lbm(vaha=profile.aktualni_vaha,
                          bodyfat=profile.procento_telesneho_tuku)
            bmr = get_bmr_advanced(lbm=lbm)
            profile.denni_kalorie = int(
                round(get_tdee(bmr=bmr, vek=profile.vek, aktivita=profile.aktivita)))
            profile.save()
            profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_macros_advanced(
                cals=profile.denni_kalorie, lbm=lbm, vaha=profile.aktualni_vaha, aktivita=profile.aktivita, vek=profile.vek)
            profile.save()
            sestav_jidelnicek(profile=profile)
            return redirect("profile")
        else:
            return redirect("info")
