from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Kunden
    path('kunden/', views.kunden_liste, name='kunden_liste'),
    path('kunden/neu/', views.kunde_neu, name='kunde_neu'),
    path('kunden/<int:pk>/', views.kunde_detail, name='kunde_detail'),
    path('kunden/<int:pk>/bearbeiten/', views.kunde_bearbeiten, name='kunde_bearbeiten'),
    path('kunden/<int:pk>/loeschen/', views.kunde_loeschen, name='kunde_loeschen'),

    # Artikel
    path('artikel/', views.artikel_liste, name='artikel_liste'),
    path('artikel/neu/', views.artikel_neu, name='artikel_neu'),
    path('artikel/<int:pk>/bearbeiten/', views.artikel_bearbeiten, name='artikel_bearbeiten'),
    path('artikel/<int:pk>/loeschen/', views.artikel_loeschen, name='artikel_loeschen'),

    # Angebote
    path('angebote/', views.angebote_liste, name='angebote_liste'),
    path('angebote/neu/', views.angebot_neu, name='angebot_neu'),
    path('angebote/<int:pk>/', views.angebot_detail, name='angebot_detail'),
    path('angebote/<int:pk>/bearbeiten/', views.angebot_bearbeiten, name='angebot_bearbeiten'),
    path('angebote/<int:pk>/pdf/', views.angebot_pdf, name='angebot_pdf'),
    path('angebote/<int:pk>/email/', views.angebot_email, name='angebot_email'),
    path('angebote/<int:pk>/email/senden/', views.angebot_email_senden, name='angebot_email_senden'),
    path('angebote/<int:pk>/in-rechnung/', views.angebot_in_rechnung, name='angebot_in_rechnung'),

    # Rechnungen
    path('rechnungen/', views.rechnungen_liste, name='rechnungen_liste'),
    path('rechnungen/neu/', views.rechnung_neu, name='rechnung_neu'),
    path('rechnungen/<int:pk>/', views.rechnung_detail, name='rechnung_detail'),
    path('rechnungen/<int:pk>/bearbeiten/', views.rechnung_bearbeiten, name='rechnung_bearbeiten'),
    path('rechnungen/<int:pk>/pdf/', views.rechnung_pdf, name='rechnung_pdf'),
    path('rechnungen/<int:pk>/email/', views.rechnung_email, name='rechnung_email'),
    path('rechnungen/<int:pk>/email/senden/', views.rechnung_email_senden, name='rechnung_email_senden'),
    path('rechnungen/<int:pk>/zahlungseingang/', views.rechnung_zahlungseingang, name='rechnung_zahlungseingang'),

    # Gutschriften
    path('gutschriften/', views.gutschriften_liste, name='gutschriften_liste'),
    path('gutschriften/neu/', views.gutschrift_neu, name='gutschrift_neu'),
    path('gutschriften/<int:pk>/', views.gutschrift_detail, name='gutschrift_detail'),
    path('gutschriften/<int:pk>/bearbeiten/', views.gutschrift_bearbeiten, name='gutschrift_bearbeiten'),
    path('gutschriften/<int:pk>/pdf/', views.gutschrift_pdf, name='gutschrift_pdf'),
    path('gutschriften/<int:pk>/email/', views.gutschrift_email, name='gutschrift_email'),
    path('gutschriften/<int:pk>/email/senden/', views.gutschrift_email_senden, name='gutschrift_email_senden'),
    path('gutschriften/<int:pk>/loeschen/', views.gutschrift_loeschen, name='gutschrift_loeschen'),
    path('rechnungen/<int:pk>/gutschrift/', views.rechnung_in_gutschrift, name='rechnung_in_gutschrift'),

    # Einstellungen
    path('einstellungen/', views.einstellungen, name='einstellungen'),
    path('datensicherung/', views.datensicherung, name='datensicherung'),
    # Artikel Daten (JSON)
    path('artikel/<int:pk>/daten/', views.artikel_daten, name='artikel_daten'),
    path('angebote/<int:pk>/loeschen/', views.angebot_loeschen, name='angebot_loeschen'),
]