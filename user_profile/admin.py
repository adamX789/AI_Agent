from django.contrib import admin
from .models import *


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("uzivatel", "denni_kalorie")


class FoodAdmin(admin.ModelAdmin):
    list_display = ("profile", "potravina")


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Food, FoodAdmin)
