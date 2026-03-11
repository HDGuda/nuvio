from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

MONATE_DE = [
    '', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

@register.filter
def datum_de(value):
    """
    Formatiert ein Datum auf Deutsch: 5. März 2026
    Funktioniert auch in WeasyPrint ohne Django-Request-Kontext.
    """
    try:
        return f"{value.day}. {MONATE_DE[value.month]} {value.year}"
    except (AttributeError, IndexError, TypeError):
        return value or '–'

@register.filter
def euro(value):
    """
    Formatiert eine Zahl als deutschen Geldbetrag.
    Beispiel: 1230.90 → 1.230,90
    """
    try:
        value = float(value)
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return value

@register.filter
def menge(value):
    """
    Formatiert eine Menge: ganze Zahlen ohne Nachkommastellen, sonst mit Komma.
    Beispiel: 1.0 → 1, 1.5 → 1,5, 2.25 → 2,25
    """
    try:
        value = float(value)
        if value == int(value):
            return str(int(value))
        else:
            return f"{value:g}".replace('.', ',')
    except (ValueError, TypeError):
        return value

@register.filter
def prozent(value):
    """
    Formatiert einen Steuersatz ohne unnötige Nachkommastellen.
    Beispiel: 19.00 → 19, 7.50 → 7,5
    """
    try:
        value = float(value)
        if value == int(value):
            return str(int(value))
        else:
            return str(value).replace('.', ',')
    except (ValueError, TypeError):
        return value

@register.filter
def platzhalter(text, objekt):
    """
    Ersetzt Platzhalter im Text durch echte Werte aus dem Angebot/Rechnung.
    Beispiel: {{kunde_firma}} → "Mustermann GmbH"
    """
    if not text:
        return text

    from core.models import Angebot, Rechnung

    werte = {}

    if hasattr(objekt, 'kunde'):
        kunde = objekt.kunde
        werte['kunde_firma'] = kunde.firma or ''
        werte['kunde_ansprechpartner'] = kunde.ansprechpartner or ''
        werte['kunde_ort'] = kunde.ort or ''

    if isinstance(objekt, Angebot):
        werte['angebot_nummer'] = objekt.nummer or ''
        werte['angebot_datum'] = objekt.datum.strftime('%d.%m.%Y') if objekt.datum else ''

    if isinstance(objekt, Rechnung):
        werte['angebot_nummer'] = objekt.nummer or ''
        werte['angebot_datum'] = objekt.datum.strftime('%d.%m.%Y') if objekt.datum else ''

    for key, val in werte.items():
        text = text.replace('{{' + key + '}}', val)

    # Seitenumbruch-Platzhalter → WeasyPrint-kompatibler Seitenumbruch
    text = text.replace('---seitenumbruch---', '<div style="page-break-after: always"></div>')

    return mark_safe(text)
