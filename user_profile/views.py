from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from chat.models import Makroziviny
from django.contrib import messages

# Create your views here.


class ProfileView(View):
    def get(self, request):
        profile = request.user.profile
        celkove_kalorie = 0
        celkove_bilkoviny = 0
        celkove_sacharidy = 0
        celkove_tuky = 0
        denni_kalorie = profile.denni_kalorie
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "kalorie": makroziviny.kalorie,
                "bilkoviny": makroziviny.bilkoviny_gramy,
                "sacharidy": makroziviny.sacharidy_gramy,
                "tuky": makroziviny.tuky_gramy,
            })
            celkove_kalorie += makroziviny.kalorie
            celkove_bilkoviny += makroziviny.bilkoviny_gramy
            celkove_sacharidy += makroziviny.sacharidy_gramy
            celkove_tuky += makroziviny.tuky_gramy
        if denni_kalorie:
            zbyvajici_kalorie = denni_kalorie - celkove_kalorie
        else:
            zbyvajici_kalorie = None
        return render(request, "profil.html", {"denni_kalorie": denni_kalorie,"zbyvajici_kalorie":zbyvajici_kalorie,"potraviny": seznam_potravin})

    def post(self, request):
        profile = request.user.profile
        try:
            kalorie = int(request.POST.get("kalorie"))
            if kalorie < 0:
                messages.error(request,"Kalorie namohou být záporné!")
            else:
                profile.denni_kalorie = kalorie
                profile.save()
        except ValueError:
            messages.error(request, "Neplatná hodnota!")

        celkove_kalorie = 0
        celkove_bilkoviny = 0
        celkove_sacharidy = 0
        celkove_tuky = 0
        denni_kalorie = profile.denni_kalorie
        seznam_potravin = []
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            seznam_potravin.append({
                "nazev": food_item.potravina.nazev,
                "kalorie": makroziviny.kalorie,
                "bilkoviny": makroziviny.bilkoviny_gramy,
                "sacharidy": makroziviny.sacharidy_gramy,
                "tuky": makroziviny.tuky_gramy,
            })
            celkove_kalorie += makroziviny.kalorie
            celkove_bilkoviny += makroziviny.bilkoviny_gramy
            celkove_sacharidy += makroziviny.sacharidy_gramy
            celkove_tuky += makroziviny.tuky_gramy
        if denni_kalorie:
            zbyvajici_kalorie = denni_kalorie - celkove_kalorie
        else:
            zbyvajici_kalorie = None
        return render(request, "profil.html", {"denni_kalorie": denni_kalorie,"zbyvajici_kalorie":zbyvajici_kalorie,"potraviny": seznam_potravin})
