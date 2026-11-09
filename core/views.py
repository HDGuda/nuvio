from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import shutil
import subprocess
from django.db.models import Count
from .models import (
    Einstellungen, Absenderprofil, RechnungGesperrt, Kunde, Artikel, ArtikelBundlePosition,
    Angebot, AngebotPosition,
    Rechnung, RechnungPosition,
    Gutschrift, GutschriftPosition,
    Zahlung,
)
from .forms import (
    AbsenderprofilForm,
    KundeForm, ArtikelForm, ArtikelBundlePositionFormSet,
    AngebotForm, AngebotPositionFormSet,
    RechnungForm, RechnungPositionFormSet,
    GutschriftForm, GutschriftPositionFormSet,
    EinstellungenForm,
    AngebotEmailForm,
    RechnungEmailForm,
    GutschriftEmailForm,
    ZahlungseingangForm,
)

from io import BytesIO
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from django.conf import settings

try:
    from weasyprint import HTML
    WEASYPRINT_VERFUEGBAR = True
except ImportError:
    WEASYPRINT_VERFUEGBAR = False

import base64 as _base64

def _logo_data_uri(logo_field):
    """Logo von der Festplatte lesen und als base64-Data-URI zurückgeben."""
    if not logo_field:
        return None
    try:
        with open(logo_field.path, 'rb') as f:
            data = _base64.b64encode(f.read()).decode('utf-8')
        ext  = logo_field.name.rsplit('.', 1)[-1].lower()
        mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png',
                'gif': 'gif', 'svg': 'svg+xml'}.get(ext, 'png')
        return f'data:image/{mime};base64,{data}'
    except Exception:
        return None

# ─────────────────────────────────────────────
#  HILFSFUNKTION: PDF-Hintergrund
# ─────────────────────────────────────────────

def pdf_mit_hintergrund(pdf_bytes, hintergrund_file):
    """
    Legt ein Hintergrund-PDF (z.B. Briefpapier) UNTER den generierten Inhalt.
    Strategie: Inhaltsseite als Basis, Hintergrund mit over=False darunter mergen.
    Liegt das Hintergrund-PDF nur auf einer Seite, wird diese wiederholt.
    Schlägt etwas fehl, wird das Original-PDF ohne Hintergrund zurückgegeben.
    """
    try:
        from pypdf import PdfWriter, PdfReader
        hintergrund = PdfReader(hintergrund_file.path)
        vordergrund = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()
        for i, inhalt_seite in enumerate(vordergrund.pages):
            bg_index = min(i, len(hintergrund.pages) - 1)
            # Seite zuerst dem Writer zuordnen, dann mergen (ab pypdf 7 vorgeschrieben)
            seite = writer.add_page(inhalt_seite)
            seite.merge_page(hintergrund.pages[bg_index], over=False)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return pdf_bytes


# ─────────────────────────────────────────────
#  HILFSFUNKTION: Seitennummern einstempeln
# ─────────────────────────────────────────────

def _tiefste_textzeile(page, untergrenze=79):
    """
    Y-Position (in pt vom unteren Seitenrand) der tiefsten Textzeile der Seite.
    Text unterhalb von 28 mm (79 pt), also der Fußzeilenbereich, wird ignoriert.
    """
    ys = []

    def visitor(text, cm, tm, font_dict, font_size):
        if text.strip():
            ys.append(cm[5] + cm[3] * tm[5])

    page.extract_text(visitor_text=visitor)
    ys = [y for y in ys if y > untergrenze]
    return min(ys) if ys else None

def seitennummern_einstempeln(pdf_bytes, y_position=686, y_folgeseiten=None, untergrenze=79):
    """
    Stempelt die korrekte Seitenzahl als Overlay auf jede Seite.
    x=538 (rechtsbündig). y_position gilt für Seite 1, y_folgeseiten (falls gesetzt)
    für alle weiteren Seiten. untergrenze: Text darunter (Fußzeile) zählt nicht
    für das Etikett "Fortsetzung auf Seite n".
    """
    try:
        from pypdf import PdfWriter, PdfReader
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        reader = PdfReader(BytesIO(pdf_bytes))
        total = len(reader.pages)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            overlay_buffer = BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=A4)
            c.setFont("Helvetica", 7.5)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            y_seite = y_position if (i == 0 or y_folgeseiten is None) else y_folgeseiten
            c.drawRightString(538, y_seite, f"Seite {i+1} von {total}")
            if i < total - 1:
                text = f"Fortsetzung auf Seite {i + 2}"
                schrift = "Helvetica"
                groesse = 6.5
                c.setFont(schrift, groesse)
                text_breite = c.stringWidth(text, schrift, groesse)

                pad = 6                          # Innenabstand links/rechts
                hoehe = 12                       # Höhe des Etiketts
                breite = text_breite + 2 * pad + 8    # +8 = Platz für den Pfeil
                x_rechts = 538
                tiefste = _tiefste_textzeile(page, untergrenze)
                if tiefste:
                    # 12 pt: Rest der Zeile bis zur Trennlinie, 14,2 pt = 5 mm Abstand
                    y = max(56, tiefste - 12 - 14.2 - hoehe)
                else:
                    y = 60

                # Etikett: helles Gold mit goldenem Rand
                c.setFillColorRGB(0.96, 0.96, 0.96)     # #f7f0e3
                c.setStrokeColorRGB(0.8, 0.8, 0.8)   # #c8a96e
                c.setLineWidth(0.5)
                c.roundRect(x_rechts - breite, y, breite, hoehe, 3, stroke=1, fill=1)

                # Text in Dunkelblau
                c.setFillColorRGB(0.102, 0.102, 0.180)     # #1a1a2e
                c.drawString(x_rechts - breite + pad, y + 3.8, text)

                # Pfeil (kleines Dreieck) am Ende
                ax = x_rechts - pad - 4
                mitte = y + hoehe / 2
                pfeil = c.beginPath()
                pfeil.moveTo(ax, mitte + 2.6)
                pfeil.lineTo(ax + 4, mitte)
                pfeil.lineTo(ax, mitte - 2.6)
                pfeil.close()
                c.drawPath(pfeil, stroke=0, fill=1)
            c.save()
            overlay_buffer.seek(0)
            overlay = PdfReader(overlay_buffer).pages[0]
            # Seite zuerst dem Writer zuordnen, dann mergen (ab pypdf 7 vorgeschrieben)
            page_neu = writer.add_page(page)
            page_neu.merge_page(overlay, over=True)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return pdf_bytes


# ─────────────────────────────────────────────
#  RECHNUNGS-PDF (Absenderprofil, Archiv)
# ─────────────────────────────────────────────

# "Seite x von y" im Rechnungs-Layout mit festem Briefkopf (pt vom unteren Seitenrand).
# Seite 1: direkt unter der Nummer/Datum-Tabelle rechts oben. Die Tabelle beginnt wegen des
# Logo-Fachs mit fester Höhe immer an derselben Stelle; jede Zeile ist 4,9 mm hoch
# (Zeilenhöhe 16,5 px + 2 px Tabellenabstand). Kalibriert: Baseline 56,3 mm bei 3 Zeilen.
# Folgeseiten: 12 mm von oben.
RECHNUNG_SEITE_Y_FOLGE = 807.9


def _rechnung_seite_y_erste(zeilen):
    baseline_mm = 56.3 - (3 - zeilen) * 4.9
    return 841.89 - baseline_mm * 72 / 25.4


def _dokument_pdf_rendern(request, template, name, objekt, zeilen):
    """
    Rendert ein Dokument (Rechnung, Angebot) frisch: Briefkopf aus dem Absenderprofil,
    Seitennummern, Briefpapier. zeilen = Zeilen der Nummer/Datum-Tabelle rechts oben.
    Liefert (pdf_bytes, html); pdf_bytes ist None ohne WeasyPrint.
    """
    einstellungen = Einstellungen.laden()
    profil = objekt.profil
    html = render_to_string(template, {
        name: objekt,
        'dokument': objekt,   # einheitlicher Name für templates/pdf_basis.html
        'einstellungen': einstellungen,
        'profil': profil,
        'logo_data_uri': _logo_data_uri(profil.logo),
    })
    if not WEASYPRINT_VERFUEGBAR:
        return None, html
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    pdf = seitennummern_einstempeln(
        pdf,
        y_position=_rechnung_seite_y_erste(zeilen),
        y_folgeseiten=RECHNUNG_SEITE_Y_FOLGE,
        untergrenze=round(profil.unterer_rand_mm * 72 / 25.4),
    )
    if profil.hintergrund_pdf:
        pdf = pdf_mit_hintergrund(pdf, profil.hintergrund_pdf)
    return pdf, html


def _rechnung_pdf_neu_rendern(request, rechnung):
    zeilen = 2 + (1 if rechnung.faellig_am else 0)
    return _dokument_pdf_rendern(request, 'rechnungen/pdf_rechnung.html', 'rechnung', rechnung, zeilen)


def _gutschrift_pdf_neu_rendern(request, gutschrift):
    zeilen = 2 + (1 if gutschrift.rechnung_id else 0)
    return _dokument_pdf_rendern(request, 'gutschriften/pdf_gutschrift.html', 'gutschrift', gutschrift, zeilen)


def _angebot_pdf_neu_rendern(request, angebot):
    zeilen = 2 + (1 if angebot.gueltig_bis else 0)
    return _dokument_pdf_rendern(request, 'angebote/pdf_angebot.html', 'angebot', angebot, zeilen)


def _rechnung_pdf_bytes(request, rechnung):
    """Archiviertes PDF (gesperrte Rechnung), sonst frisch gerendert. Gibt (pdf, html) zurück."""
    if rechnung.pdf_archiv:
        try:
            with rechnung.pdf_archiv.open('rb') as f:
                return f.read(), None
        except (OSError, ValueError):
            pass
    return _rechnung_pdf_neu_rendern(request, rechnung)


def _rechnung_archivieren(request, rechnung, pdf=None):
    """
    Friert das PDF einer gesperrten Rechnung einmalig ein.
    Wird pdf übergeben (z. B. das gerade versendete PDF), wird genau dieses archiviert.
    """
    if not rechnung.ist_gesperrt or rechnung.pdf_archiv:
        return
    if pdf is None:
        pdf, _html = _rechnung_pdf_neu_rendern(request, rechnung)
    if pdf:
        rechnung.pdf_archiv.save(f'Rechnung_{rechnung.nummer}.pdf', ContentFile(pdf), save=False)
        rechnung.save(update_fields=['pdf_archiv'])


def _gutschrift_pdf_bytes(request, gutschrift):
    """Archiviertes PDF (gesperrte Gutschrift), sonst frisch gerendert. Gibt (pdf, html) zurück."""
    if gutschrift.pdf_archiv:
        try:
            with gutschrift.pdf_archiv.open('rb') as f:
                return f.read(), None
        except (OSError, ValueError):
            pass
    return _gutschrift_pdf_neu_rendern(request, gutschrift)


def _gutschrift_archivieren(request, gutschrift, pdf=None):
    """
    Friert das PDF einer gesperrten Gutschrift einmalig ein.
    Wird pdf übergeben (z. B. das gerade versendete PDF), wird genau dieses archiviert.
    """
    if not gutschrift.ist_gesperrt or gutschrift.pdf_archiv:
        return
    if pdf is None:
        pdf, _html = _gutschrift_pdf_neu_rendern(request, gutschrift)
    if pdf:
        gutschrift.pdf_archiv.save(f'Gutschrift_{gutschrift.nummer}.pdf', ContentFile(pdf), save=False)
        gutschrift.save(update_fields=['pdf_archiv'])


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

def dashboard(request):
    context = {
        'angebote_offen':     Angebot.objects.filter(status__in=['entwurf', 'gesendet']).count(),
        'rechnungen_offen':   Rechnung.objects.filter(status__in=['entwurf', 'gesendet']).count(),
        'rechnungen_bezahlt': Rechnung.objects.filter(status='bezahlt').count(),
        'letzte_angebote':    Angebot.objects.select_related('kunde').order_by('-erstellt_am')[:5],
        'letzte_rechnungen':  Rechnung.objects.select_related('kunde').order_by('-erstellt_am')[:5],
    }
    return render(request, 'dashboard.html', context)


# ─────────────────────────────────────────────
#  KUNDEN
# ─────────────────────────────────────────────

def kunden_liste(request):
    from django.db.models.functions import Coalesce
    from django.db.models import Value
    suche = request.GET.get('suche', '')
    kunden = Kunde.objects.all()
    if suche:
        kunden = kunden.filter(firma__icontains=suche) \
                | kunden.filter(nachname__icontains=suche) \
                | kunden.filter(vorname__icontains=suche)
    from django.db.models.functions import NullIf
    kunden = kunden.annotate(
        sort_key=Coalesce(NullIf('firma', Value('')), 'nachname')
    ).order_by('sort_key', 'vorname')
    return render(request, 'kunden/liste.html', {'kunden': kunden, 'suche': suche})


def kunde_detail(request, pk):
    kunde = get_object_or_404(Kunde, pk=pk)
    angebote = Angebot.objects.filter(kunde=kunde).order_by('-datum')
    rechnungen = Rechnung.objects.filter(kunde=kunde).order_by('-datum')
    return render(request, 'kunden/detail.html', {
        'kunde': kunde,
        'angebote': angebote,
        'rechnungen': rechnungen
    })


def kunde_neu(request):
    if request.method == 'POST':
        form = KundeForm(request.POST)
        if form.is_valid():
            kunde = form.save()
            messages.success(request, f'Kunde „{kunde}" wurde angelegt.')
            return redirect('kunden_liste')
    else:
        form = KundeForm()
    return render(request, 'kunden/formular.html', {'form': form, 'titel': 'Neuer Kunde'})


def kunde_bearbeiten(request, pk):
    kunde = get_object_or_404(Kunde, pk=pk)
    if request.method == 'POST':
        form = KundeForm(request.POST, instance=kunde)
        if form.is_valid():
            form.save()
            messages.success(request, f'Kunde „{kunde}" wurde gespeichert.')
            return redirect('kunden_liste')
    else:
        form = KundeForm(instance=kunde)
    return render(request, 'kunden/formular.html', {'form': form, 'titel': 'Kunde bearbeiten'})


def kunde_loeschen(request, pk):
    kunde = get_object_or_404(Kunde, pk=pk)
    if request.method == 'POST':
        name = str(kunde)
        kunde.delete()
        messages.success(request, f'Kunde „{name}" wurde gelöscht.')
        return redirect('kunden_liste')
    return render(request, 'kunden/loeschen.html', {'kunde': kunde})


# ─────────────────────────────────────────────
#  ARTIKEL
# ─────────────────────────────────────────────

def artikel_liste(request):
    artikel = (
        Artikel.objects.filter(aktiv=True)
        .prefetch_related('bundle_positionen__artikel')
    )
    return render(request, 'artikel/liste.html', {'artikel': artikel})


def artikel_neu(request):
    if request.method == 'POST':
        form    = ArtikelForm(request.POST)
        formset = ArtikelBundlePositionFormSet(request.POST, prefix='bundle')
        if form.is_valid() and formset.is_valid():
            artikel          = form.save()
            formset.instance = artikel
            formset.save()
            messages.success(request, f'Artikel „{artikel}" wurde angelegt.')
            return redirect('artikel_liste')
    else:
        form    = ArtikelForm()
        formset = ArtikelBundlePositionFormSet(prefix='bundle')
    return render(request, 'artikel/formular.html', {
        'form':    form,
        'formset': formset,
        'titel':   'Neuer Artikel',
    })


def artikel_bearbeiten(request, pk):
    artikel = get_object_or_404(Artikel, pk=pk)
    if request.method == 'POST':
        form    = ArtikelForm(request.POST, instance=artikel)
        formset = ArtikelBundlePositionFormSet(
            request.POST, instance=artikel, prefix='bundle'
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Artikel „{artikel}" wurde gespeichert.')
            return redirect('artikel_liste')
    else:
        form    = ArtikelForm(instance=artikel)
        formset = ArtikelBundlePositionFormSet(instance=artikel, prefix='bundle')
    return render(request, 'artikel/formular.html', {
        'form':    form,
        'formset': formset,
        'titel':   'Artikel bearbeiten',
    })


def artikel_loeschen(request, pk):
    artikel = get_object_or_404(Artikel, pk=pk)
    if request.method == 'POST':
        artikel.aktiv = False  # Soft-Delete: Artikel wird nur deaktiviert
        artikel.save()
        messages.success(request, f'Artikel „{artikel}" wurde gelöscht.')
        return redirect('artikel_liste')
    return render(request, 'artikel/loeschen.html', {'artikel': artikel})


# ─────────────────────────────────────────────
#  ANGEBOTE
# ─────────────────────────────────────────────

def angebote_liste(request):
    status_filter = request.GET.get('status', '')
    angebote = Angebot.objects.select_related('kunde').all()
    if status_filter:
        angebote = angebote.filter(status=status_filter)
    return render(request, 'angebote/liste.html', {
        'angebote': angebote,
        'status_filter': status_filter,
        'status_choices': Angebot.STATUS_CHOICES
    })


def angebot_detail(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    return render(request, 'angebote/detail.html', {'angebot': angebot})


def angebot_neu(request):
    AngebotPositionFormSet.extra = 1
    if request.method == 'POST':
        form = AngebotForm(request.POST)
        formset = AngebotPositionFormSet(request.POST, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            angebot = form.save()
            formset.instance = angebot
            formset.save()
            messages.success(request, f'Angebot „{angebot.nummer}" wurde erstellt.')
            return redirect('angebot_detail', pk=angebot.pk)
    else:
        einstellungen = Einstellungen.laden()
        form = AngebotForm(initial={
            'einleitungstext': einstellungen.angebot_einleitung,
            'schlusstext':     einstellungen.angebot_schlusstext,
        })
        formset = AngebotPositionFormSet(prefix='positionen')
    return render(request, 'angebote/formular.html', {
        'form':    form,
        'formset': formset,
        'titel':   'Neues Angebot',
        'kleinunternehmer': Einstellungen.laden().kleinunternehmer,
    })


def angebot_bearbeiten(request, pk):
    AngebotPositionFormSet.extra = 0
    angebot = get_object_or_404(Angebot, pk=pk)
    if request.method == 'POST':
        form = AngebotForm(request.POST, instance=angebot)
        formset = AngebotPositionFormSet(request.POST, instance=angebot, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Angebot „{angebot.nummer}" wurde gespeichert.')
            return redirect('angebot_detail', pk=angebot.pk)
    else:
        form = AngebotForm(instance=angebot)
        formset = AngebotPositionFormSet(instance=angebot, prefix='positionen')
    return render(request, 'angebote/formular.html', {
        'form': form,
        'formset': formset,
        'titel': 'Angebot bearbeiten',
        'angebot': angebot,
        'kleinunternehmer': angebot.kleinunternehmer,
    })


def angebot_pdf(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    pdf, html = _angebot_pdf_neu_rendern(request, angebot)
    if pdf is None:
        return HttpResponse(html)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Angebot_{angebot.nummer}.pdf"'
    return response


# ─────────────────────────────────────────────
#  ANGEBOT PER E-MAIL VERSENDEN
# ─────────────────────────────────────────────

def _html_zu_plaintext(html):
    """
    Wandelt gespeichertes HTML (aus contenteditable) in lesbaren Plaintext um.
    <div>, <p>, <br> → Zeilenumbrüche, alle anderen Tags werden entfernt.
    """
    import re
    from html import unescape
    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _plaintext_zu_html(text):
    """Wandelt Plaintext in HTML um: \n → <br>, damit Zeilenumbrüche erhalten bleiben."""
    from html import escape
    return escape(text).replace('\n', '<br>\n')


# ─────────────────────────────────────────────
#  E-MAIL-ÜBERGABE AN THUNDERBIRD
# ─────────────────────────────────────────────

class ThunderbirdFehler(Exception):
    """Thunderbird wurde nicht gefunden oder konnte nicht gestartet werden."""


def _thunderbird_pfad():
    """
    Sucht thunderbird.exe: zuerst die Django-Einstellung THUNDERBIRD_PFAD (optional),
    dann den PATH, dann die üblichen Installationsorte.
    """
    kandidaten = [getattr(settings, 'THUNDERBIRD_PFAD', '') or '', shutil.which('thunderbird') or '']
    for var in ('ProgramFiles', 'ProgramFiles(x86)'):
        basis = os.environ.get(var)
        if basis:
            kandidaten.append(os.path.join(basis, 'Mozilla Thunderbird', 'thunderbird.exe'))
    lokal = os.environ.get('LOCALAPPDATA')
    if lokal:
        kandidaten.append(os.path.join(lokal, 'Programs', 'Mozilla Thunderbird', 'thunderbird.exe'))
    for pfad in kandidaten:
        if pfad and os.path.isfile(pfad):
            return pfad
    raise ThunderbirdFehler(
        'thunderbird.exe wurde nicht gefunden. Pfad bei Bedarf in den Django-Einstellungen '
        '(settings.py) als THUNDERBIRD_PFAD angeben.'
    )


def _tb_text(text):
    """Einzeiliger Wert für die Kommandozeile: einfache Anführungszeichen (Wertbegrenzer) werden ersetzt."""
    text = (text or '').replace("'", '’').replace('"', '”')
    return ' '.join(text.split())


def _tb_body(text):
    """HTML-Text für die Kommandozeile: Anführungszeichen werden zu Entitäten, Zeilenumbrüche zu <br>."""
    from html import escape
    text = escape((text or '').replace('\r\n', '\n').replace('\r', '\n'))
    return text.replace('\n', '<br>')


def _thunderbird_oeffnen(profil, empfaenger, betreff, text, anhaenge):
    """
    Öffnet in Thunderbird ein neues Schreibfenster mit Empfänger, Betreff, Text und Anhängen.
    Die Identität (Absenderadresse) kommt aus dem Absenderprofil (preselectid, z. B. id2).
    Versendet wird erst, wenn du in Thunderbird auf „Senden“ klickst.
    """
    pfad = _thunderbird_pfad()
    for datei in anhaenge:
        if ',' in datei or "'" in datei:
            raise ThunderbirdFehler(
                f'Der Dateiname „{os.path.basename(datei)}“ enthält ein Komma oder einen Apostroph '
                'und lässt sich so nicht an Thunderbird übergeben. Bitte die Datei umbenennen.'
            )
    teile = [
        f"to='{_tb_text(empfaenger).replace(';', ',')}'",
        f"subject='{_tb_text(betreff)}'",
        "format='html'",
        f"body='{_tb_body(text)}'",
        f"attachment='{','.join(anhaenge)}'",
    ]
    identitaet = (profil.thunderbird_identitaet or '').strip()
    if identitaet:
        teile.insert(0, f"preselectid='{identitaet}'")
    try:
        subprocess.Popen([pfad, '-compose', ','.join(teile)])
    except OSError as e:
        raise ThunderbirdFehler(f'Thunderbird konnte nicht gestartet werden: {e}')


def _betreff_ersetzen(vorlage, angebot, einstellungen, firma=None):
    """Ersetzt Platzhalter in der Betreff-Vorlage."""
    kunde = angebot.kunde
    kundenname = kunde.firma or kunde.ansprechpartner or ''
    return (vorlage
        .replace('{{nummer}}', angebot.nummer)
        .replace('{{kundenname}}', kundenname)
        .replace('{{firma}}', (firma if firma is not None else einstellungen.firma_name) or '')
        .replace('{{datum}}', angebot.datum.strftime('%d.%m.%Y') if angebot.datum else ''))


def angebot_email(request, pk):
    """Zeigt die E-Mail-Vorschau mit vorausgefülltem Formular."""
    angebot = get_object_or_404(Angebot, pk=pk)
    einstellungen = Einstellungen.laden()

    betreff = _betreff_ersetzen(
        einstellungen.email_angebot_betreff or f'Angebot {angebot.nummer}',
        angebot, einstellungen, firma=angebot.profil.firma_anzeige
    )

    rohtext = einstellungen.email_angebot_text or ''
    if '<' in rohtext:
        rohtext = _html_zu_plaintext(rohtext)

    initial = {
        'empfaenger':   angebot.kunde.email or '',
        'betreff':      betreff,
        'text':         rohtext,
        'anhang1_aktiv': bool(einstellungen.email_angebot_anhang1),
        'anhang2_aktiv': bool(einstellungen.email_angebot_anhang2),
    }
    form = AngebotEmailForm(initial=initial)

    return render(request, 'angebote/email.html', {
        'angebot':        angebot,
        'einstellungen':  einstellungen,
        'form':           form,
    })


def angebot_email_senden(request, pk):
    """Generiert die PDF und übergibt die E-Mail an Thunderbird."""
    import tempfile, os, time
    angebot = get_object_or_404(Angebot, pk=pk)
    einstellungen = Einstellungen.laden()

    if request.method != 'POST':
        return redirect('angebot_email', pk=pk)

    form = AngebotEmailForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'angebote/email.html', {
            'angebot': angebot,
            'einstellungen': einstellungen,
            'form': form,
        })

    # ── PDF generieren ──
    pdf_bytes, _html = _angebot_pdf_neu_rendern(request, angebot)
    if pdf_bytes is None:
        messages.error(request, 'WeasyPrint nicht verfügbar – PDF konnte nicht generiert werden.')
        return redirect('angebot_detail', pk=pk)

    # ── PDF in temporäre Datei speichern ──
    tmp_dir = tempfile.gettempdir()
    pdf_pfad = os.path.join(tmp_dir, f'Angebot_{angebot.nummer}.pdf')
    with open(pdf_pfad, 'wb') as f:
        f.write(pdf_bytes)

    # ── Anhänge zusammenstellen ──
    anhaenge = [pdf_pfad]

    if form.cleaned_data.get('anhang1_aktiv') and einstellungen.email_angebot_anhang1:
        anhaenge.append(einstellungen.email_angebot_anhang1.path)

    if form.cleaned_data.get('anhang2_aktiv') and einstellungen.email_angebot_anhang2:
        anhaenge.append(einstellungen.email_angebot_anhang2.path)

    if form.cleaned_data.get('extra_anhang'):
        extra = form.cleaned_data['extra_anhang']
        extra_pfad = os.path.join(tmp_dir, extra.name)
        with open(extra_pfad, 'wb') as f:
            for chunk in extra.chunks():
                f.write(chunk)
        anhaenge.append(extra_pfad)

    # ── In Thunderbird öffnen ──
    try:
        _thunderbird_oeffnen(
            angebot.profil,
            form.cleaned_data['empfaenger'],
            form.cleaned_data['betreff'],
            form.cleaned_data['text'],
            anhaenge,
        )
        if angebot.status == 'entwurf':
            angebot.status = 'gesendet'
            angebot.gesendet_am = timezone.now().date()
            angebot.save(update_fields=['status', 'gesendet_am'])
    except ThunderbirdFehler as e:
        messages.error(request, str(e))
        return redirect('angebot_detail', pk=pk)

    messages.success(request, f'E-Mail für Angebot {angebot.nummer} wurde an Thunderbird übergeben.')
    return redirect('angebot_detail', pk=pk)


def angebot_in_rechnung(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    rechnung = angebot.in_rechnung_umwandeln()
    messages.success(request, f'Rechnung „{rechnung.nummer}" wurde aus Angebot erstellt. Bitte prüfen und speichern.')
    return redirect('rechnung_bearbeiten', pk=rechnung.pk)


def angebot_annehmen(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    if request.method == 'POST':
        angebot.status = 'angenommen'
        angebot.save(update_fields=['status'])
        messages.success(request, f'Angebot „{angebot.nummer}" wurde als angenommen markiert.')
    return redirect('angebot_detail', pk=pk)


# ─────────────────────────────────────────────
#  RECHNUNG PER E-MAIL VERSENDEN
# ─────────────────────────────────────────────

def rechnung_email(request, pk):
    """Zeigt die E-Mail-Vorschau für eine Rechnung."""
    rechnung = get_object_or_404(Rechnung, pk=pk)
    einstellungen = Einstellungen.laden()

    betreff = _betreff_ersetzen(
        einstellungen.email_rechnung_betreff or f'Rechnung {rechnung.nummer}',
        rechnung, einstellungen, firma=rechnung.profil.firma_anzeige
    )

    rohtext = einstellungen.email_rechnung_text or ''
    if '<' in rohtext:
        rohtext = _html_zu_plaintext(rohtext)

    initial = {
        'empfaenger':    rechnung.kunde.email or '',
        'betreff':       betreff,
        'text':          rohtext,
        'anhang1_aktiv': bool(einstellungen.email_rechnung_anhang1),
        'anhang2_aktiv': bool(einstellungen.email_rechnung_anhang2),
    }
    form = RechnungEmailForm(initial=initial)

    return render(request, 'rechnungen/email.html', {
        'rechnung':      rechnung,
        'einstellungen': einstellungen,
        'form':          form,
    })


def rechnung_email_senden(request, pk):
    """Generiert die PDF und übergibt die Rechnungs-E-Mail an Thunderbird."""
    import tempfile, os
    rechnung = get_object_or_404(Rechnung, pk=pk)
    einstellungen = Einstellungen.laden()

    if request.method != 'POST':
        return redirect('rechnung_email', pk=pk)

    form = RechnungEmailForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'rechnungen/email.html', {
            'rechnung': rechnung,
            'einstellungen': einstellungen,
            'form': form,
        })

    # ── PDF (Archiv bei gesperrter Rechnung, sonst frisch) ──
    pdf_bytes, _html = _rechnung_pdf_bytes(request, rechnung)
    if pdf_bytes is None:
        messages.error(request, 'WeasyPrint nicht verfügbar – PDF konnte nicht generiert werden.')
        return redirect('rechnung_detail', pk=pk)

    tmp_dir = tempfile.gettempdir()
    pdf_pfad = os.path.join(tmp_dir, f'Rechnung_{rechnung.nummer}.pdf')
    with open(pdf_pfad, 'wb') as f:
        f.write(pdf_bytes)

    anhaenge = [pdf_pfad]
    if form.cleaned_data.get('anhang1_aktiv') and einstellungen.email_rechnung_anhang1:
        anhaenge.append(einstellungen.email_rechnung_anhang1.path)
    if form.cleaned_data.get('anhang2_aktiv') and einstellungen.email_rechnung_anhang2:
        anhaenge.append(einstellungen.email_rechnung_anhang2.path)
    if form.cleaned_data.get('extra_anhang'):
        extra = form.cleaned_data['extra_anhang']
        extra_pfad = os.path.join(tmp_dir, extra.name)
        with open(extra_pfad, 'wb') as f:
            for chunk in extra.chunks():
                f.write(chunk)
        anhaenge.append(extra_pfad)

    try:
        _thunderbird_oeffnen(
            rechnung.profil,
            form.cleaned_data['empfaenger'],
            form.cleaned_data['betreff'],
            form.cleaned_data['text'],
            anhaenge,
        )
        if rechnung.status == 'entwurf':
            rechnung.status = 'gesendet'
            rechnung.gesendet_am = timezone.now().date()
            rechnung.save(update_fields=['status', 'gesendet_am'])
        # GoBD: ab "Gesendet" sperren und genau das versendete PDF archivieren
        if rechnung.sperren_falls_versendet():
            _rechnung_archivieren(request, rechnung, pdf_bytes)
    except ThunderbirdFehler as e:
        messages.error(request, str(e))
        return redirect('rechnung_detail', pk=pk)

    messages.success(request, f'E-Mail für Rechnung {rechnung.nummer} wurde an Thunderbird übergeben.')
    return redirect('rechnung_detail', pk=pk)


# ─────────────────────────────────────────────
#  GUTSCHRIFT PER E-MAIL VERSENDEN
# ─────────────────────────────────────────────

def gutschrift_email(request, pk):
    """Zeigt die E-Mail-Vorschau für eine Gutschrift."""
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    einstellungen = Einstellungen.laden()

    betreff = _betreff_ersetzen(
        einstellungen.email_gutschrift_betreff or f'Gutschrift {gutschrift.nummer}',
        gutschrift, einstellungen, firma=gutschrift.profil.firma_anzeige
    )

    rohtext = einstellungen.email_gutschrift_text or ''
    if '<' in rohtext:
        rohtext = _html_zu_plaintext(rohtext)

    initial = {
        'empfaenger':    gutschrift.kunde.email or '',
        'betreff':       betreff,
        'text':          rohtext,
        'anhang1_aktiv': bool(einstellungen.email_gutschrift_anhang1),
        'anhang2_aktiv': bool(einstellungen.email_gutschrift_anhang2),
    }
    form = GutschriftEmailForm(initial=initial)

    return render(request, 'gutschriften/email.html', {
        'gutschrift':    gutschrift,
        'einstellungen': einstellungen,
        'form':          form,
    })


def gutschrift_email_senden(request, pk):
    """Generiert die PDF und übergibt die Gutschrift-E-Mail an Thunderbird."""
    import tempfile, os
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    einstellungen = Einstellungen.laden()

    if request.method != 'POST':
        return redirect('gutschrift_email', pk=pk)

    form = GutschriftEmailForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'gutschriften/email.html', {
            'gutschrift': gutschrift,
            'einstellungen': einstellungen,
            'form': form,
        })

    # ── PDF (Archiv bei gesperrter Gutschrift, sonst frisch) ──
    pdf_bytes, _html = _gutschrift_pdf_bytes(request, gutschrift)
    if pdf_bytes is None:
        messages.error(request, 'WeasyPrint nicht verfügbar – PDF konnte nicht generiert werden.')
        return redirect('gutschrift_detail', pk=pk)

    tmp_dir = tempfile.gettempdir()
    pdf_pfad = os.path.join(tmp_dir, f'Gutschrift_{gutschrift.nummer}.pdf')
    with open(pdf_pfad, 'wb') as f:
        f.write(pdf_bytes)

    anhaenge = [pdf_pfad]
    if form.cleaned_data.get('anhang1_aktiv') and einstellungen.email_gutschrift_anhang1:
        anhaenge.append(einstellungen.email_gutschrift_anhang1.path)
    if form.cleaned_data.get('anhang2_aktiv') and einstellungen.email_gutschrift_anhang2:
        anhaenge.append(einstellungen.email_gutschrift_anhang2.path)
    if form.cleaned_data.get('extra_anhang'):
        extra = form.cleaned_data['extra_anhang']
        extra_pfad = os.path.join(tmp_dir, extra.name)
        with open(extra_pfad, 'wb') as f:
            for chunk in extra.chunks():
                f.write(chunk)
        anhaenge.append(extra_pfad)

    try:
        _thunderbird_oeffnen(
            gutschrift.profil,
            form.cleaned_data['empfaenger'],
            form.cleaned_data['betreff'],
            form.cleaned_data['text'],
            anhaenge,
        )
        if gutschrift.status == 'entwurf':
            gutschrift.status = 'gesendet'
            gutschrift.save(update_fields=['status'])
        # GoBD: ab "Gesendet" sperren und genau das versendete PDF archivieren
        if gutschrift.sperren_falls_versendet():
            _gutschrift_archivieren(request, gutschrift, pdf_bytes)
    except ThunderbirdFehler as e:
        messages.error(request, str(e))
        return redirect('gutschrift_detail', pk=pk)

    messages.success(request, f'E-Mail für Gutschrift {gutschrift.nummer} wurde an Thunderbird übergeben.')
    return redirect('gutschrift_detail', pk=pk)


# ─────────────────────────────────────────────
#  RECHNUNGEN
# ─────────────────────────────────────────────

def rechnungen_liste(request):
    status_filter = request.GET.get('status', '')
    rechnungen = Rechnung.objects.select_related('kunde').all()
    if status_filter:
        rechnungen = rechnungen.filter(status=status_filter)
    return render(request, 'rechnungen/liste.html', {
        'rechnungen': rechnungen,
        'status_filter': status_filter,
        'status_choices': Rechnung.STATUS_CHOICES
    })


def rechnung_detail(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    offen = rechnung.offener_betrag
    zahlungsformular = ZahlungseingangForm(initial={
        'bezahlt_am':     timezone.now().date(),
        'bezahlt_betrag': offen if offen > 0 else rechnung.brutto,
    })
    return render(request, 'rechnungen/detail.html', {
        'rechnung':         rechnung,
        'zahlungsformular': zahlungsformular,
    })


def rechnung_zahlungseingang(request, pk):
    """Speichert Zahlungseingang als eigenes Zahlung-Objekt und setzt Status automatisch."""
    rechnung = get_object_or_404(Rechnung, pk=pk)
    if request.method != 'POST':
        return redirect('rechnung_detail', pk=pk)

    if rechnung.offener_betrag <= 0:
        messages.warning(request, f'Rechnung „{rechnung.nummer}" ist bereits vollständig bezahlt bzw. ausgeglichen.')
        return redirect('rechnung_detail', pk=pk)

    form = ZahlungseingangForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Bitte Datum und Betrag korrekt eingeben.')
        return redirect('rechnung_detail', pk=pk)

    zahlung = Zahlung.objects.create(
        rechnung=rechnung,
        datum=form.cleaned_data['bezahlt_am'],
        betrag=form.cleaned_data['bezahlt_betrag'],
    )

    if rechnung.offener_betrag <= 0:
        rechnung.status = 'bezahlt'
    else:
        rechnung.status = 'teilbezahlt'
    rechnung.save(update_fields=['status'])
    if rechnung.sperren_falls_versendet():
        _rechnung_archivieren(request, rechnung)

    messages.success(request, f'Zahlungseingang von {zahlung.betrag} € wurde gespeichert.')
    return redirect('rechnung_detail', pk=pk)


def rechnung_neu(request):
    RechnungPositionFormSet.extra = 1
    if request.method == 'POST':
        form = RechnungForm(request.POST)
        formset = RechnungPositionFormSet(request.POST, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            rechnung = form.save()
            formset.instance = rechnung
            formset.save()
            if rechnung.sperren_falls_versendet():
                _rechnung_archivieren(request, rechnung)
            messages.success(request, f'Rechnung „{rechnung.nummer}" wurde angelegt.')
            return redirect('rechnung_detail', pk=rechnung.pk)
    else:
        form = RechnungForm()
        formset = RechnungPositionFormSet(prefix='positionen')
    artikel = Artikel.objects.filter(aktiv=True).order_by('bezeichnung')
    return render(request, 'rechnungen/formular.html', {
        'form': form,
        'formset': formset,
        'titel': 'Neue Rechnung',
        'artikel_liste': artikel,
        'kleinunternehmer': Einstellungen.laden().kleinunternehmer,
    })


def rechnung_bearbeiten(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    if rechnung.ist_gesperrt:
        messages.warning(
            request,
            f'Rechnung „{rechnung.nummer}" ist versendet und damit gesperrt (GoBD). '
            'Korrekturen sind nur per Gutschrift und neuer Rechnung möglich.'
        )
        return redirect('rechnung_detail', pk=pk)
    RechnungPositionFormSet.extra = 0
    if request.method == 'POST':
        form = RechnungForm(request.POST, instance=rechnung)
        formset = RechnungPositionFormSet(request.POST, instance=rechnung, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            if rechnung.sperren_falls_versendet():
                _rechnung_archivieren(request, rechnung)
            messages.success(request, f'Rechnung „{rechnung.nummer}" wurde gespeichert.')
            return redirect('rechnung_detail', pk=rechnung.pk)
    else:
        form = RechnungForm(instance=rechnung)
        formset = RechnungPositionFormSet(instance=rechnung, prefix='positionen')
    artikel = Artikel.objects.filter(aktiv=True).order_by('bezeichnung')
    return render(request, 'rechnungen/formular.html', {
        'form': form,
        'formset': formset,
        'titel': 'Rechnung bearbeiten',
        'artikel_liste': artikel,
        'rechnung': rechnung,
        'kleinunternehmer': rechnung.kleinunternehmer,
    })


def rechnung_pdf(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    _rechnung_archivieren(request, rechnung)  # gesperrte Rechnungen werden beim ersten Abruf eingefroren
    pdf, html = _rechnung_pdf_bytes(request, rechnung)
    if pdf is None:
        return HttpResponse(html)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Rechnung_{rechnung.nummer}.pdf"'
    return response


# ─────────────────────────────────────────────
#  ABSENDERPROFILE
# ─────────────────────────────────────────────

def absenderprofile_liste(request):
    Absenderprofil.standard()  # stellt sicher, dass mindestens ein Profil existiert
    profile = Absenderprofil.objects.annotate(
        anzahl_rechnungen=Count('rechnungen', distinct=True),
        anzahl_angebote=Count('angebote', distinct=True),
        anzahl_gutschriften=Count('gutschriften', distinct=True),
    )
    return render(request, 'absenderprofile/liste.html', {'profile': profile})


def absenderprofil_neu(request):
    form = AbsenderprofilForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        profil = form.save()
        messages.success(request, f'Absenderprofil „{profil.name}\" wurde angelegt.')
        return redirect('absenderprofile_liste')
    return render(request, 'absenderprofile/formular.html', {
        'form': form, 'titel': 'Neues Absenderprofil',
    })


def absenderprofil_bearbeiten(request, pk):
    profil = get_object_or_404(Absenderprofil, pk=pk)
    form = AbsenderprofilForm(request.POST or None, request.FILES or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Absenderprofil „{profil.name}\" wurde gespeichert.')
        return redirect('absenderprofile_liste')
    return render(request, 'absenderprofile/formular.html', {
        'form': form, 'profil': profil, 'titel': 'Absenderprofil bearbeiten',
    })


def absenderprofil_standard(request, pk):
    profil = get_object_or_404(Absenderprofil, pk=pk)
    if request.method == 'POST':
        profil.ist_standard = True
        profil.save()  # setzt bei allen anderen Profilen ist_standard zurück
        messages.success(request, f'„{profil.name}\" ist jetzt das Standardprofil.')
    return redirect('absenderprofile_liste')


def absenderprofil_loeschen(request, pk):
    profil = get_object_or_404(Absenderprofil, pk=pk)
    anzahl = profil.rechnungen.count() + profil.angebote.count() + profil.gutschriften.count()
    grund = None
    if profil.ist_standard:
        grund = 'Das Standardprofil kann nicht gelöscht werden. Lege zuerst ein anderes Profil als Standard fest.'
    elif anzahl:
        grund = f'Das Profil wird von {anzahl} Dokument(en) verwendet und kann nicht gelöscht werden.'
    if request.method == 'POST' and not grund:
        name = profil.name
        profil.delete()
        messages.success(request, f'Absenderprofil „{name}\" wurde gelöscht.')
        return redirect('absenderprofile_liste')
    return render(request, 'absenderprofile/loeschen.html', {'profil': profil, 'grund': grund})


# ─────────────────────────────────────────────
#  EINSTELLUNGEN
# ─────────────────────────────────────────────

def einstellungen(request):
    obj = Einstellungen.laden()
    if request.method == 'POST':
        form = EinstellungenForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Einstellungen wurden gespeichert.')
            return redirect('einstellungen')
    else:
        form = EinstellungenForm(instance=obj)
    return render(request, 'einstellungen.html', {'form': form})


# ─────────────────────────────────────────────
#  DATENSICHERUNG
# ─────────────────────────────────────────────

def _datenbank_snapshot(db_pfad, ziel_pfad):
    """
    Konsistente Kopie der SQLite-Datenbank über die Backup-Funktion von SQLite.
    Anders als ein reines Dateikopieren ist das Ergebnis auch bei laufendem
    Betrieb (gleichzeitiger Schreibzugriff) garantiert in sich stimmig.
    """
    quelle = sqlite3.connect(str(db_pfad))
    ziel = sqlite3.connect(ziel_pfad)
    try:
        quelle.backup(ziel)
    finally:
        ziel.close()
        quelle.close()


def datensicherung(request):
    buffer = BytesIO()

    with tempfile.TemporaryDirectory() as tmp_dir, \
            zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Datenbank (als Snapshot, nicht als Dateikopie)
        db_pfad = settings.DATABASES['default']['NAME']
        if os.path.exists(db_pfad):
            snapshot_pfad = os.path.join(tmp_dir, 'db.sqlite3')
            _datenbank_snapshot(db_pfad, snapshot_pfad)
            zf.write(snapshot_pfad, 'db.sqlite3')

        # Media-Ordner
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for ordner, unterordner, dateien in os.walk(media_root):
                for datei in dateien:
                    voller_pfad = os.path.join(ordner, datei)
                    relativer_pfad = os.path.relpath(voller_pfad, media_root)
                    zf.write(voller_pfad, os.path.join('media', relativer_pfad))

    buffer.seek(0)
    zeitstempel = datetime.now().strftime('%Y%m%d_%H%M%S')
    dateiname = f'Nuvio_Backup_{zeitstempel}.zip'

    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{dateiname}"'
    return response


# ─────────────────────────────────────────────
#  ARTIKEL DATEN (JSON für Formular)
# ─────────────────────────────────────────────

def artikel_daten(request, pk):
    artikel = get_object_or_404(Artikel, pk=pk)

    if artikel.is_bundle:
        positionen = []
        for bp in artikel.aktive_bundle_positionen():
            positionen.append({
                'bezeichnung': bp.artikel.bezeichnung,
                'beschreibung': bp.artikel.beschreibung,
                'einheit':      bp.artikel.einheit,
                'einzelpreis':  str(bp.artikel.einzelpreis),
                'steuersatz':   str(bp.artikel.steuersatz),
                'menge':        str(bp.menge),
            })
        return JsonResponse({'is_bundle': True, 'positionen': positionen})

    return JsonResponse({
        'is_bundle':    False,
        'bezeichnung':  artikel.bezeichnung,
        'beschreibung': artikel.beschreibung,
        'einheit':      artikel.einheit,
        'einzelpreis':  str(artikel.einzelpreis),
        'steuersatz':   str(artikel.steuersatz),
    })


def angebot_loeschen(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    if Rechnung.objects.filter(angebot=angebot).exists():
        messages.error(request, f'Angebot „{angebot.nummer}" kann nicht gelöscht werden, da bereits eine Rechnung dazu existiert.')
        return redirect('angebot_detail', pk=angebot.pk)
    if request.method == 'POST':
        nummer = angebot.nummer
        angebot.delete()
        messages.success(request, f'Angebot „{nummer}" wurde gelöscht.')
        return redirect('angebote_liste')
    return render(request, 'angebote/loeschen.html', {'angebot': angebot})


# ─────────────────────────────────────────────
#  GUTSCHRIFTEN
# ─────────────────────────────────────────────

def gutschriften_liste(request):
    gutschriften = Gutschrift.objects.select_related('kunde', 'rechnung').all()
    return render(request, 'gutschriften/liste.html', {'gutschriften': gutschriften})


def gutschrift_detail(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    return render(request, 'gutschriften/detail.html', {'gutschrift': gutschrift})


def gutschrift_neu(request):
    GutschriftPositionFormSet.extra = 1
    if request.method == 'POST':
        form = GutschriftForm(request.POST)
        formset = GutschriftPositionFormSet(request.POST, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            gutschrift = form.save()
            formset.instance = gutschrift
            formset.save()
            if gutschrift.sperren_falls_versendet():
                _gutschrift_archivieren(request, gutschrift)
            if gutschrift.rechnung:
                gutschrift.rechnung.gutschrift_status_aktualisieren()
            messages.success(request, f'Gutschrift „{gutschrift.nummer}" wurde angelegt.')
            return redirect('gutschrift_detail', pk=gutschrift.pk)
    else:
        form = GutschriftForm()
        formset = GutschriftPositionFormSet(prefix='positionen')
    artikel = Artikel.objects.filter(aktiv=True).order_by('bezeichnung')
    return render(request, 'gutschriften/formular.html', {
        'form': form,
        'formset': formset,
        'titel': 'Neue Gutschrift',
        'artikel_liste': artikel,
        'kleinunternehmer': Einstellungen.laden().kleinunternehmer,
    })


def gutschrift_bearbeiten(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    if gutschrift.ist_gesperrt:
        messages.warning(
            request,
            f'Gutschrift „{gutschrift.nummer}" ist versendet und damit gesperrt (GoBD). '
            'Korrekturen sind nur per neuer Gutschrift möglich.'
        )
        return redirect('gutschrift_detail', pk=pk)
    GutschriftPositionFormSet.extra = 0
    if request.method == 'POST':
        form = GutschriftForm(request.POST, instance=gutschrift)
        formset = GutschriftPositionFormSet(request.POST, instance=gutschrift, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            if gutschrift.sperren_falls_versendet():
                _gutschrift_archivieren(request, gutschrift)
            if gutschrift.rechnung:
                gutschrift.rechnung.gutschrift_status_aktualisieren()
            messages.success(request, f'Gutschrift „{gutschrift.nummer}" wurde gespeichert.')
            return redirect('gutschrift_detail', pk=gutschrift.pk)
    else:
        form = GutschriftForm(instance=gutschrift)
        formset = GutschriftPositionFormSet(instance=gutschrift, prefix='positionen')
    artikel = Artikel.objects.filter(aktiv=True).order_by('bezeichnung')
    return render(request, 'gutschriften/formular.html', {
        'form': form,
        'formset': formset,
        'titel': 'Gutschrift bearbeiten',
        'artikel_liste': artikel,
        'kleinunternehmer': gutschrift.kleinunternehmer,
    })


def gutschrift_pdf(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    _gutschrift_archivieren(request, gutschrift)  # gesperrte Gutschriften werden beim ersten Abruf eingefroren
    pdf, html = _gutschrift_pdf_bytes(request, gutschrift)
    if pdf is None:
        return HttpResponse(html)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Gutschrift_{gutschrift.nummer}.pdf"'
    return response


def rechnung_in_gutschrift(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    gutschrift = Gutschrift(
        kunde=rechnung.kunde,
        rechnung=rechnung,
        betreff=f'Gutschrift zu {rechnung.nummer}',
        einleitungstext=rechnung.einleitungstext,
        schlusstext=rechnung.schlusstext,
    )
    gutschrift.save()
    for position in rechnung.positionen.all():
        GutschriftPosition.objects.create(
            gutschrift=gutschrift,
            bezeichnung=position.bezeichnung,
            beschreibung=position.beschreibung,
            menge=position.menge,
            einheit=position.einheit,
            einzelpreis=position.einzelpreis,
            steuersatz=position.steuersatz,
        )
    rechnung.gutschrift_status_aktualisieren()
    messages.success(request, f'Gutschrift „{gutschrift.nummer}" wurde erstellt. Bitte prüfen und speichern.')
    return redirect('gutschrift_bearbeiten', pk=gutschrift.pk)


def gutschrift_loeschen(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    if gutschrift.ist_gesperrt:
        messages.warning(
            request,
            f'Gutschrift „{gutschrift.nummer}" ist versendet und damit gesperrt (GoBD) und kann nicht gelöscht werden.'
        )
        return redirect('gutschrift_detail', pk=pk)
    if request.method == 'POST':
        nummer = gutschrift.nummer
        gutschrift.delete()  # delete() in models.py aktualisiert automatisch den Rechnungsstatus
        messages.success(request, f'Gutschrift „{nummer}" wurde gelöscht.')
        return redirect('gutschriften_liste')
    return render(request, 'gutschriften/loeschen.html', {'gutschrift': gutschrift})
