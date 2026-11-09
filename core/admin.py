from django.contrib import admin
from .models import (
    Einstellungen, Absenderprofil, Kunde, Artikel,
    Vorlage, Angebot, AngebotPosition,
    Rechnung, RechnungPosition
)

@admin.register(Einstellungen)
class EinstellungenAdmin(admin.ModelAdmin):
    pass

@admin.register(Absenderprofil)
class AbsenderprofilAdmin(admin.ModelAdmin):
    list_display = ['name', 'ist_standard', 'firmenname', 'thunderbird_identitaet']

@admin.register(Kunde)
class KundeAdmin(admin.ModelAdmin):
    list_display = ['firma', 'ansprechpartner', 'email', 'telefon']
    search_fields = ['firma', 'ansprechpartner', 'email']

@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ['bezeichnung', 'preis', 'steuersatz', 'aktiv']
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # GoBD: auch im Admin gilt die Sperre ab "Gesendet" (jeder Status außer "Entwurf")
        obj.sperren_falls_versendet()