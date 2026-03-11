from django.contrib import admin
from .models import (
    Einstellungen, Kunde, Artikel,
    Vorlage, Angebot, AngebotPosition,
    Rechnung, RechnungPosition
)

@admin.register(Einstellungen)
class EinstellungenAdmin(admin.ModelAdmin):
    pass

@admin.register(Kunde)
class KundeAdmin(admin.ModelAdmin):
    list_display = ['firma', 'ansprechpartner', 'email', 'telefon']
    search_fields = ['firma', 'ansprechpartner', 'email']

@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ['bezeichnung', 'einzelpreis', 'steuersatz', 'aktiv']
    search_fields = ['bezeichnung']

@admin.register(Angebot)
class AngebotAdmin(admin.ModelAdmin):
    list_display = ['nummer', 'kunde', 'datum', 'status']
    list_filter = ['status']
    search_fields = ['nummer', 'kunde__firma']

@admin.register(Rechnung)
class RechnungAdmin(admin.ModelAdmin):
    list_display = ['nummer', 'kunde', 'datum', 'faellig_am', 'status']
    list_filter = ['status']
    search_fields = ['nummer', 'kunde__firma']