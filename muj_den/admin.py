from django.contrib import admin
from .models import Jidelnicek, JidelnicekRecept

# Vytvoření Inline třídy
class JidelnicekReceptInline(admin.TabularInline):
    model = JidelnicekRecept
    extra = 1  # Počet prázdných formulářů pro přidání nových záznamů

# Registrace modelu Jidelnicek s Inline třídou
@admin.register(Jidelnicek)
class JidelnicekAdmin(admin.ModelAdmin):
    list_display = ['profile']  # Co se má zobrazit v seznamu jídelníčků
    inlines = [JidelnicekReceptInline]

# Nezapomeňte také zaregistrovat samotný JidelnicekRecept, pokud ho chcete mít v administraci zvlášť
@admin.register(JidelnicekRecept)
class JidelnicekReceptAdmin(admin.ModelAdmin):
    list_display = ['jidelnicek', 'recept', 'chod', 'scale_factor', 'snezeno']
    list_filter = ['jidelnicek', 'chod']
    search_fields = ['recept__nazev']
