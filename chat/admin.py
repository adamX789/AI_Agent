from django.contrib import admin
from .models import *

class AktivitaAdmin(admin.ModelAdmin):
    list_display = ("typ_aktivity", "kategorie", "met_hodnota", "popis")

class MessageAdmin(admin.ModelAdmin):
    list_display = ("text", "sender", "role", "time_sent")


class PotravinyAdmin(admin.ModelAdmin):
    list_display = ("nazev", "popis", "vyhody",
                    "nejlepsi_pro", "nekonzumujte_pokud")


class MakrozivinyAdmin(admin.ModelAdmin):
    list_display = ("potravina", "kalorie", "bilkoviny_gramy",
                    "sacharidy_gramy", "tuky_gramy")

class MakrozivinyReceptyAdmin(admin.ModelAdmin):
    list_display = ("recept", "kalorie", "bilkoviny_gramy",
                    "sacharidy_gramy", "tuky_gramy")


class ReceptyAdmin(admin.ModelAdmin):
    list_display = ("nazev", "ingredience", "instrukce", "vhodne_pro")


class SituaceAdmin(admin.ModelAdmin):
    list_display = ("popis_situace", "rada")


class DietyAdmin(admin.ModelAdmin):
    list_display = ("nazev_diety", "popis", "vyhody", "neni_doporuceno_pro")


class StylyKomunikaceAdmin(admin.ModelAdmin):
    list_display = ("styl", "priklad")


admin.site.register(Aktivita,AktivitaAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Potraviny, PotravinyAdmin)
admin.site.register(Makroziviny, MakrozivinyAdmin)
admin.site.register(MakrozivinyRecepty, MakrozivinyReceptyAdmin)
admin.site.register(Recepty, ReceptyAdmin)
admin.site.register(Situace, SituaceAdmin)
admin.site.register(Diety, DietyAdmin)
admin.site.register(StylyKomunikace, StylyKomunikaceAdmin)
