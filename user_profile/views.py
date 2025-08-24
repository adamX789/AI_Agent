from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from chat.models import Makroziviny
from django.contrib import messages

# Create your views here.


def get_cals_and_macros(pohlavi, vek, aktivita, vyska, vaha, cil):
    if pohlavi == "Muž":
        bmr = 88.362 + (13.397*vaha) + (4.799*vyska) - (5.677*vek)
    else:
        bmr = 447.593 + (9.247*vaha) + (3.098*vyska) - (4.330*vek)

    if aktivita == "Nízká aktivita":
        tdee = bmr*1.2
    elif aktivita == "Střední aktivita":
        tdee = bmr*1.55
    else:
        tdee = bmr*1.725

    if cil == "Nabrat":
        denni_kalorie = int(round(tdee+300, 0))
    elif cil == "Udržet":
        denni_kalorie = int(round(tdee-400, 0))
    else:
        denni_kalorie = int(round(tdee, 0))

    denni_bilkoviny = int(round(vaha*2, 0))
    denni_tuky = int(round((denni_kalorie*0.25)/9, 0))
    denni_sacharidy = int(
        round((denni_kalorie - (denni_bilkoviny*4) - (denni_tuky*9))/4, 0))
    pitny_rezim = round((vaha*37.5)/1000, 2)
    return denni_kalorie, denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim


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


class FormView(View):
    def get(self, request):
        return render(request, "form.html", {})

    def post(self, request):
        profile = request.user.profile
        profile.jmeno = request.POST.get("jmeno")
        profile.vek = 19
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
        profile.vyska_v_cm = float(request.POST.get("vyska"))
        profile.aktualni_vaha = float(request.POST.get("vaha"))
        profile.cilova_vaha = float(request.POST.get("cilova_vaha"))
        cil = request.POST.get("cil")
        if cil == "n":
            profile.celkovy_cil = "Nabrat"
        elif cil == "u":
            profile.celkovy_cil = "Udržet"
        elif cil == "z":
            profile.celkovy_cil = "Zhubnout"
        else:
            messages.error(request, "Prosím vyberte cíl.")
            return render(request, "form.html", {})
        aktivita = request.POST.get("aktivita")
        if aktivita == "nizka":
            profile.aktivita = "Nízká aktivita"
        elif aktivita == "stredni":
            profile.aktivita = "Střední aktivita"
        elif aktivita == "vysoka":
            profile.aktivita = "Vysoká aktivita"
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

        profile.denni_kalorie, profile.denni_bilkoviny, profile.denni_sacharidy, profile.denni_tuky, profile.pitny_rezim_litry = get_cals_and_macros(
            pohlavi=profile.pohlavi, vek=profile.vek, aktivita=profile.aktivita, vyska=profile.vyska_v_cm, vaha=profile.aktualni_vaha, cil=profile.celkovy_cil)
        profile.save()
        return redirect("profile")
