from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import (
    Einstellungen, Kunde, Artikel,
    Angebot, AngebotPosition,
    Rechnung, RechnungPosition,
    Gutschrift, GutschriftPosition,
)
from .forms import (
    KundeForm, ArtikelForm,
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
import zipfile
from datetime import datetime
from django.conf import settings

try:
    from weasyprint import HTML
    WEASYPRINT_VERFUEGBAR = True
except ImportError:
    WEASYPRINT_VERFUEGBAR = False


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
        import copy
        hintergrund = PdfReader(hintergrund_file.path)
        vordergrund = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()
        for i, inhalt_seite in enumerate(vordergrund.pages):
            bg_index = min(i, len(hintergrund.pages) - 1)
            seite = copy.copy(inhalt_seite)
            seite.merge_page(hintergrund.pages[bg_index], over=False)
            writer.add_page(seite)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return pdf_bytes


# ─────────────────────────────────────────────
#  HILFSFUNKTION: Seitennummern einstempeln
# ─────────────────────────────────────────────

def seitennummern_einstempeln(pdf_bytes, y_position=686):
    """
    Stempelt die korrekte Seitenzahl als Overlay auf jede Seite.
    x=538 (rechtsbündig), y_position variiert je nach Anzahl der Metazeilen.
    """
    try:
        from pypdf import PdfWriter, PdfReader
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import copy
        reader = PdfReader(BytesIO(pdf_bytes))
        total = len(reader.pages)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            overlay_buffer = BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=A4)
            c.setFont("Helvetica", 7.5)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawRightString(538, y_position, f"Seite {i+1} von {total}")
            c.save()
            overlay_buffer.seek(0)
            overlay = PdfReader(overlay_buffer).pages[0]
            page_copy = copy.copy(page)
            page_copy.merge_page(overlay, over=True)
            writer.add_page(page_copy)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return pdf_bytes


def _seiten_y_gutschrift(zeilen_vor_seite):
    """
    Wie _seiten_y, aber kalibriert für Gutschriften.
    Basis: 2 Zeilen (Nummer, Datum) → y=669.
    """
    basis_zeilen = 2
    basis_y = 700.5
    zeilen_hoehe = 15
    extra = zeilen_vor_seite - basis_zeilen
    return basis_y - (extra * zeilen_hoehe)


def _seiten_y(zeilen_vor_seite):
    """
    Berechnet die reportlab-Y-Koordinate der 'Seite'-Zeile.
    Kalibriert am funktionierenden Angebot mit BAFA-Nummer:
      y=686 bei 3 Zeilen vor 'Seite' (Nummer, Datum, BAFA-Nummer).
    Jede Zeile weniger → +16.5pt (eine Zeilenhöhe nach oben).
    """
    basis_zeilen = 3  # Angebot mit BAFA: Nummer, Datum, BAFA-Nummer
    basis_y = 686
    zeilen_hoehe = 16.5
    extra = zeilen_vor_seite - basis_zeilen
    return basis_y - (extra * zeilen_hoehe)


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
    suche = request.GET.get('suche', '')
    kunden = Kunde.objects.all()
    if suche:
        kunden = kunden.filter(firma__icontains=suche) | kunden.filter(ansprechpartner__icontains=suche)
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
    artikel = Artikel.objects.filter(aktiv=True)
    return render(request, 'artikel/liste.html', {'artikel': artikel})


def artikel_neu(request):
    if request.method == 'POST':
        form = ArtikelForm(request.POST)
        if form.is_valid():
            artikel = form.save()
            messages.success(request, f'Artikel „{artikel}" wurde angelegt.')
            return redirect('artikel_liste')
    else:
        form = ArtikelForm()
    return render(request, 'artikel/formular.html', {'form': form, 'titel': 'Neuer Artikel'})


def artikel_bearbeiten(request, pk):
    artikel = get_object_or_404(Artikel, pk=pk)
    if request.method == 'POST':
        form = ArtikelForm(request.POST, instance=artikel)
        if form.is_valid():
            form.save()
            messages.success(request, f'Artikel „{artikel}" wurde gespeichert.')
            return redirect('artikel_liste')
    else:
        form = ArtikelForm(instance=artikel)
    return render(request, 'artikel/formular.html', {'form': form, 'titel': 'Artikel bearbeiten'})


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
        formset = AngebotPositionFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            angebot = form.save()
            formset.instance = angebot
            formset.save()
            messages.success(request, f'Angebot „{angebot.nummer}" wurde erstellt.')
            return redirect('angebot_detail', pk=angebot.pk)
    else:
        # Standardtexte aus Einstellungen laden
        einstellungen = Einstellungen.laden()
        form = AngebotForm(initial={
            'einleitungstext': einstellungen.angebot_einleitung,
            'schlusstext':     einstellungen.angebot_schlusstext,
        })
        formset = AngebotPositionFormSet()
    return render(request, 'angebote/formular.html', {
        'form':    form,
        'formset': formset,
        'titel':   'Neues Angebot',
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
    })


def angebot_pdf(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    einstellungen = Einstellungen.laden()
    html = render_to_string('angebote/pdf.html', {
        'angebot': angebot,
        'einstellungen': einstellungen
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        # Zeilen VOR 'Seite': Nummer, Datum, [Gültig bis], [BAFA-Nummer]
        zeilen = 2
        if angebot.gueltig_bis:
            zeilen += 1
        if einstellungen.firma_zusatz2:
            zeilen += 1
        pdf = seitennummern_einstempeln(pdf, y_position=_seiten_y(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf = pdf_mit_hintergrund(pdf, einstellungen.hintergrund_pdf)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="Angebot_{angebot.nummer}.pdf"'
        return response
    else:
        return HttpResponse(html)




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
    """
    Wandelt Plaintext für mail.HTMLBody vor: \n → <br>, damit
    Outlook Zeilenumbrüche korrekt darstellt.
    """
    from html import escape
    return escape(text).replace('\n', '<br>\n')


def _betreff_ersetzen(vorlage, angebot, einstellungen):
    """Ersetzt Platzhalter in der Betreff-Vorlage."""
    kunde = angebot.kunde
    kundenname = kunde.firma or kunde.ansprechpartner or ''
    return (vorlage
        .replace('{{nummer}}', angebot.nummer)
        .replace('{{kundenname}}', kundenname)
        .replace('{{firma}}', einstellungen.firma_name or '')
        .replace('{{datum}}', angebot.datum.strftime('%d.%m.%Y') if angebot.datum else ''))


def angebot_email(request, pk):
    """Zeigt die E-Mail-Vorschau mit vorausgefülltem Formular."""
    angebot = get_object_or_404(Angebot, pk=pk)
    einstellungen = Einstellungen.laden()

    betreff = _betreff_ersetzen(
        einstellungen.email_angebot_betreff or f'Angebot {angebot.nummer}',
        angebot, einstellungen
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
    """Generiert die PDF und übergibt die E-Mail an Outlook."""
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
    html = render_to_string('angebote/pdf.html', {
        'angebot': angebot,
        'einstellungen': einstellungen,
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf_bytes = HTML(string=html, base_url=base_url).write_pdf()
        zeilen = 2
        if angebot.gueltig_bis:
            zeilen += 1
        if einstellungen.firma_zusatz2:
            zeilen += 1
        pdf_bytes = seitennummern_einstempeln(pdf_bytes, y_position=_seiten_y(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf_bytes = pdf_mit_hintergrund(pdf_bytes, einstellungen.hintergrund_pdf)
    else:
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

    # ── Outlook per COM öffnen ──
    try:
        import win32com.client, subprocess, time, pythoncom
        pythoncom.CoInitialize()
        outlook_pfad = r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"
        subprocess.Popen([outlook_pfad])
        time.sleep(3)
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)  # 0 = olMailItem
        mail.To       = form.cleaned_data['empfaenger']
        mail.Subject  = form.cleaned_data['betreff']
        mail.HTMLBody = _plaintext_zu_html(form.cleaned_data['text'])
        for pfad in anhaenge:
            mail.Attachments.Add(pfad)
        mail.Display(True)  # True = modales Fenster
        if angebot.status == 'entwurf':
            angebot.status = 'gesendet'
            angebot.gesendet_am = timezone.now().date()
            angebot.save(update_fields=['status', 'gesendet_am'])
    except ImportError:
        messages.error(request, 'pywin32 ist nicht installiert. Bitte "pip install pywin32" im venv ausführen.')
        return redirect('angebot_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Outlook konnte nicht geöffnet werden: {e}')
        return redirect('angebot_detail', pk=pk)

    messages.success(request, f'E-Mail für Angebot {angebot.nummer} wurde an Outlook übergeben.')
    return redirect('angebot_detail', pk=pk)


def angebot_in_rechnung(request, pk):
    angebot = get_object_or_404(Angebot, pk=pk)
    rechnung = angebot.in_rechnung_umwandeln()
    messages.success(request, f'Rechnung „{rechnung.nummer}" wurde aus Angebot erstellt. Bitte prüfen und speichern.')
    return redirect('rechnung_bearbeiten', pk=rechnung.pk)


# ─────────────────────────────────────────────
#  RECHNUNG PER E-MAIL VERSENDEN
# ─────────────────────────────────────────────

def rechnung_email(request, pk):
    """Zeigt die E-Mail-Vorschau für eine Rechnung."""
    rechnung = get_object_or_404(Rechnung, pk=pk)
    einstellungen = Einstellungen.laden()

    betreff = _betreff_ersetzen(
        einstellungen.email_rechnung_betreff or f'Rechnung {rechnung.nummer}',
        rechnung, einstellungen
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
    """Generiert die PDF und übergibt die Rechnungs-E-Mail an Outlook."""
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

    # ── PDF generieren ──
    html = render_to_string('rechnungen/pdf.html', {
        'rechnung': rechnung,
        'einstellungen': einstellungen,
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf_bytes = HTML(string=html, base_url=base_url).write_pdf()
        zeilen = 2
        if rechnung.faellig_am:
            zeilen += 1
        if einstellungen.firma_zusatz2:
            zeilen += 1
        pdf_bytes = seitennummern_einstempeln(pdf_bytes, y_position=_seiten_y(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf_bytes = pdf_mit_hintergrund(pdf_bytes, einstellungen.hintergrund_pdf)
    else:
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
        import win32com.client, subprocess, time, pythoncom
        pythoncom.CoInitialize()
        outlook_pfad = r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"
        subprocess.Popen([outlook_pfad])
        time.sleep(3)
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.To       = form.cleaned_data['empfaenger']
        mail.Subject  = form.cleaned_data['betreff']
        mail.HTMLBody = _plaintext_zu_html(form.cleaned_data['text'])
        for pfad in anhaenge:
            mail.Attachments.Add(pfad)
        mail.Display(True)
        if rechnung.status == 'entwurf':
            rechnung.status = 'gesendet'
            rechnung.gesendet_am = timezone.now().date()
            rechnung.save(update_fields=['status', 'gesendet_am'])
    except ImportError:
        messages.error(request, 'pywin32 ist nicht installiert.')
        return redirect('rechnung_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Outlook konnte nicht geöffnet werden: {e}')
        return redirect('rechnung_detail', pk=pk)

    messages.success(request, f'E-Mail für Rechnung {rechnung.nummer} wurde an Outlook übergeben.')
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
        gutschrift, einstellungen
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
    """Generiert die PDF und übergibt die Gutschrift-E-Mail an Outlook."""
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

    # ── PDF generieren ──
    html = render_to_string('gutschriften/pdf.html', {
        'gutschrift': gutschrift,
        'einstellungen': einstellungen,
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf_bytes = HTML(string=html, base_url=base_url).write_pdf()
        zeilen = 2
        if gutschrift.rechnung:
            zeilen += 1
        pdf_bytes = seitennummern_einstempeln(pdf_bytes, y_position=_seiten_y(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf_bytes = pdf_mit_hintergrund(pdf_bytes, einstellungen.hintergrund_pdf)
    else:
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
        import win32com.client, subprocess, time, pythoncom
        pythoncom.CoInitialize()
        outlook_pfad = r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"
        subprocess.Popen([outlook_pfad])
        time.sleep(3)
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.To       = form.cleaned_data['empfaenger']
        mail.Subject  = form.cleaned_data['betreff']
        mail.HTMLBody = _plaintext_zu_html(form.cleaned_data['text'])
        for pfad in anhaenge:
            mail.Attachments.Add(pfad)
        mail.Display(True)
        if gutschrift.status == 'entwurf':
            gutschrift.status = 'gesendet'
            gutschrift.save(update_fields=['status'])
    except ImportError:
        messages.error(request, 'pywin32 ist nicht installiert.')
        return redirect('gutschrift_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Outlook konnte nicht geöffnet werden: {e}')
        return redirect('gutschrift_detail', pk=pk)

    messages.success(request, f'E-Mail für Gutschrift {gutschrift.nummer} wurde an Outlook übergeben.')
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
    zahlungsformular = ZahlungseingangForm(initial={
        'bezahlt_am':     rechnung.bezahlt_am or timezone.now().date(),
        'bezahlt_betrag': rechnung.bezahlt_betrag or rechnung.brutto,
    })
    return render(request, 'rechnungen/detail.html', {
        'rechnung':         rechnung,
        'zahlungsformular': zahlungsformular,
    })


def rechnung_zahlungseingang(request, pk):
    """Speichert Zahlungseingang und setzt Status automatisch."""
    rechnung = get_object_or_404(Rechnung, pk=pk)
    if request.method != 'POST':
        return redirect('rechnung_detail', pk=pk)

    form = ZahlungseingangForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Bitte Datum und Betrag korrekt eingeben.')
        return redirect('rechnung_detail', pk=pk)

    rechnung.bezahlt_am     = form.cleaned_data['bezahlt_am']
    rechnung.bezahlt_betrag = form.cleaned_data['bezahlt_betrag']

    if rechnung.bezahlt_betrag >= rechnung.brutto:
        rechnung.status = 'bezahlt'
    else:
        rechnung.status = 'teilbezahlt'

    rechnung.save(update_fields=['bezahlt_am', 'bezahlt_betrag', 'status'])
    messages.success(request, f'Zahlungseingang von {rechnung.bezahlt_betrag} € wurde gespeichert.')
    return redirect('rechnung_detail', pk=pk)


def rechnung_neu(request):
    # 1 leere Position als Startpunkt
    RechnungPositionFormSet.extra = 1
    if request.method == 'POST':
        form = RechnungForm(request.POST)
        formset = RechnungPositionFormSet(request.POST, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            rechnung = form.save()
            formset.instance = rechnung
            formset.save()
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
    })


def rechnung_bearbeiten(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    # Nur bestehende Positionen, keine leere Extrazeile
    RechnungPositionFormSet.extra = 0
    if request.method == 'POST':
        form = RechnungForm(request.POST, instance=rechnung)
        formset = RechnungPositionFormSet(request.POST, instance=rechnung, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
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
    })


def rechnung_pdf(request, pk):
    rechnung = get_object_or_404(Rechnung, pk=pk)
    einstellungen = Einstellungen.laden()
    html = render_to_string('rechnungen/pdf.html', {
        'rechnung': rechnung,
        'einstellungen': einstellungen
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        # Zeilen VOR 'Seite': Nummer, Datum, [Fällig am], [BAFA-Nummer]
        zeilen = 2
        if rechnung.faellig_am:
            zeilen += 1
        if einstellungen.firma_zusatz2:
            zeilen += 1
        pdf = seitennummern_einstempeln(pdf, y_position=_seiten_y(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf = pdf_mit_hintergrund(pdf, einstellungen.hintergrund_pdf)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="Rechnung_{rechnung.nummer}.pdf"'
        return response
    else:
        return HttpResponse(html)


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

def datensicherung(request):
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Datenbank
        db_pfad = settings.DATABASES['default']['NAME']
        if os.path.exists(db_pfad):
            zf.write(db_pfad, 'db.sqlite3')

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
    return JsonResponse({
        'bezeichnung': artikel.bezeichnung,
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
    })


def gutschrift_bearbeiten(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    GutschriftPositionFormSet.extra = 0
    if request.method == 'POST':
        form = GutschriftForm(request.POST, instance=gutschrift)
        formset = GutschriftPositionFormSet(request.POST, instance=gutschrift, prefix='positionen')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
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
    })


def gutschrift_pdf(request, pk):
    gutschrift = get_object_or_404(Gutschrift, pk=pk)
    einstellungen = Einstellungen.laden()
    html = render_to_string('gutschriften/pdf.html', {
        'gutschrift': gutschrift,
        'einstellungen': einstellungen,
    })
    if WEASYPRINT_VERFUEGBAR:
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        # Zeilen VOR 'Seite': Nummer, Datum, [Zu Rechnung]
        zeilen = 2
        if gutschrift.rechnung:
            zeilen += 1
        pdf = seitennummern_einstempeln(pdf, y_position=_seiten_y_gutschrift(zeilen))
        if einstellungen.hintergrund_pdf:
            pdf = pdf_mit_hintergrund(pdf, einstellungen.hintergrund_pdf)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="Gutschrift_{gutschrift.nummer}.pdf"'
        return response
    else:
        return HttpResponse(html)


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
    if request.method == 'POST':
        nummer = gutschrift.nummer
        gutschrift.delete()  # delete() in models.py aktualisiert automatisch den Rechnungsstatus
        messages.success(request, f'Gutschrift „{nummer}" wurde gelöscht.')
        return redirect('gutschriften_liste')
    return render(request, 'gutschriften/loeschen.html', {'gutschrift': gutschrift})
