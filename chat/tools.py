from django.db.models.expressions import RawSQL
from .models import *
from user_profile.models import Food


def search_potraviny(profile, user_embedding, update: bool, pocet_vysledku=3):
    nejrelevantnejsi_potraviny = Potraviny.objects.annotate(podoba=RawSQL(
        "%s::vector <=> embedding", (user_embedding,))).order_by("podoba")[:pocet_vysledku]
    dict_list = []
    for potravina in nejrelevantnejsi_potraviny:
        if potravina.podoba < 0.35:
            makroziviny = Makroziviny.objects.get(potravina=potravina)
            print(f"potravina: {potravina.nazev}, podoba: {potravina.podoba}")
            dict_list.append(
                {
                    "nazev": potravina.nazev,
                    "popis": potravina.popis,
                    "kalorie": makroziviny.kalorie,
                    "bilkoviny_gramy": str(makroziviny.bilkoviny_gramy),
                    "sacharidy_gramy": str(makroziviny.sacharidy_gramy),
                    "tuky_gramy": str(makroziviny.tuky_gramy),
                    "vyhody": potravina.vyhody,
                    "nejlepsi_pro": potravina.nejlepsi_pro,
                    "nekonzumujte_pokud": potravina.nekonzumujte_pokud
                }
            )
    if update:
        for potravina in nejrelevantnejsi_potraviny:
            if potravina.podoba < 0.35:
                profile.food_set.create(potravina=potravina)
    return dict_list
