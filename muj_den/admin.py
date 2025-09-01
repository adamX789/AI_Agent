from django.contrib import admin
from .models import *


class JidelnicekAdmin(admin.ModelAdmin):
    list_display = ("profile", "display_snidane", "display_svacina1", "display_obedy", "display_svacina2", "display_vecere")

    def display_snidane(self, obj):
        # Spojí názvy všech receptů v tomto ManyToManyField a vrátí je jako řetězec
        return ", ".join([recept.nazev for recept in obj.seznam_snidani.all()])
    
    def display_svacina1(self, obj):
        return ", ".join([recept.nazev for recept in obj.seznam_svacin1.all()])

    def display_obedy(self, obj):
        return ", ".join([recept.nazev for recept in obj.seznam_obedu.all()])
        
    def display_svacina2(self, obj):
        return ", ".join([recept.nazev for recept in obj.seznam_svacin2.all()])

    def display_vecere(self, obj):
        return ", ".join([recept.nazev for recept in obj.seznam_veceri.all()])


class VybraneReceptyAdmin(admin.ModelAdmin):
    list_display = ("profile", "snidane", "svacina1",
                    "obed", "svacina2", "vecere")


admin.site.register(Jidelnicek, JidelnicekAdmin)
admin.site.register(VybraneRecepty, VybraneReceptyAdmin)
