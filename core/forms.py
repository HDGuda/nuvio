from django import forms
from django.forms import inlineformset_factory
from .models import (
    Einstellungen, Kunde, Artikel,
    Angebot, AngebotPosition,
    Rechnung, RechnungPosition
)


# ─────────────────────────────────────────────
#  EINSTELLUNGEN
# ─────────────────────────────────────────────

class EinstellungenForm(forms.ModelForm):
    class Meta:
        model = Einstellungen
        fields = [
            'firma_name', 'firma_zusatz', 'firma_zusatz2',
            'strasse', 'plz', 'ort',
            'telefon', 'email', 'website', 'logo', 'hintergrund_pdf',
            'steuernummer', 'ust_id',
            'bank_name', 'iban', 'bic',
            'angebot_prefix', 'angebot_naechste_nummer', 'angebot_format',
            'rechnung_prefix', 'rechnung_naechste_nummer', 'rechnung_format',
            'gutschrift_prefix', 'gutschrift_naechste_nummer', 'gutschrift_format',
            'angebot_einleitung', 'angebot_schlusstext',
            'rechnung_einleitung', 'rechnung_schlusstext',
            'zahlungsbedingungen',
            'email_angebot_betreff', 'email_angebot_text',
            'email_angebot_anhang1', 'email_angebot_anhang2',
            'email_rechnung_betreff', 'email_rechnung_text',
            'email_rechnung_anhang1', 'email_rechnung_anhang2',
            'email_gutschrift_betreff', 'email_gutschrift_text',
            'email_gutschrift_anhang1', 'email_gutschrift_anhang2',
        ]
        widgets = {
            'angebot_einleitung':    forms.Textarea(attrs={'rows': 3}),
            'angebot_schlusstext':   forms.Textarea(attrs={'rows': 3}),
            'rechnung_einleitung':   forms.Textarea(attrs={'rows': 3}),
            'rechnung_schlusstext':  forms.Textarea(attrs={'rows': 3}),
            'zahlungsbedingungen':   forms.Textarea(attrs={'rows': 2}),
            'email_angebot_text':    forms.Textarea(attrs={'rows': 6}),
            'email_rechnung_text':   forms.Textarea(attrs={'rows': 6}),
            'email_gutschrift_text': forms.Textarea(attrs={'rows': 6}),
        }


# ─────────────────────────────────────────────
#  E-MAIL ANGEBOT (Vorschau-Formular)
# ─────────────────────────────────────────────

class AngebotEmailForm(forms.Form):
    empfaenger      = forms.EmailField(label='Empfänger', widget=forms.EmailInput(attrs={'style': 'width: 100%;'}))
    betreff         = forms.CharField(label='Betreff', max_length=200, widget=forms.TextInput(attrs={'style': 'width: 100%;'}))
    text            = forms.CharField(label='E-Mail-Text', widget=forms.Textarea(attrs={'rows': 10, 'style': 'width: 100%;'}))
    anhang1_aktiv   = forms.BooleanField(label='Anhang 1 mitsenden', required=False, initial=True)
    anhang2_aktiv   = forms.BooleanField(label='Anhang 2 mitsenden', required=False, initial=True)
    extra_anhang    = forms.FileField(label='Zusätzlicher Anhang', required=False)


class RechnungEmailForm(forms.Form):
    empfaenger      = forms.EmailField(label='Empfänger', widget=forms.EmailInput(attrs={'style': 'width: 100%;'}))
    betreff         = forms.CharField(label='Betreff', max_length=200, widget=forms.TextInput(attrs={'style': 'width: 100%;'}))
    text            = forms.CharField(label='E-Mail-Text', widget=forms.Textarea(attrs={'rows': 10, 'style': 'width: 100%;'}))
    anhang1_aktiv   = forms.BooleanField(label='Anhang 1 mitsenden', required=False, initial=True)
    anhang2_aktiv   = forms.BooleanField(label='Anhang 2 mitsenden', required=False, initial=True)
    extra_anhang    = forms.FileField(label='Zusätzlicher Anhang', required=False)


class GutschriftEmailForm(forms.Form):
    empfaenger      = forms.EmailField(label='Empfänger', widget=forms.EmailInput(attrs={'style': 'width: 100%;'}))
    betreff         = forms.CharField(label='Betreff', max_length=200, widget=forms.TextInput(attrs={'style': 'width: 100%;'}))
    text            = forms.CharField(label='E-Mail-Text', widget=forms.Textarea(attrs={'rows': 10, 'style': 'width: 100%;'}))
    anhang1_aktiv   = forms.BooleanField(label='Anhang 1 mitsenden', required=False, initial=True)
    anhang2_aktiv   = forms.BooleanField(label='Anhang 2 mitsenden', required=False, initial=True)
    extra_anhang    = forms.FileField(label='Zusätzlicher Anhang', required=False)


# ─────────────────────────────────────────────
#  KUNDE
# ─────────────────────────────────────────────

class KundeForm(forms.ModelForm):
    class Meta:
        model = Kunde
        fields = [
            'firma', 'ansprechpartner',
            'strasse', 'plz', 'ort', 'land',
            'email', 'telefon', 'website',
            'ust_id', 'notizen',
        ]
        widgets = {
            'notizen': forms.Textarea(attrs={'rows': 3}),
        }


# ─────────────────────────────────────────────
#  ARTIKEL
# ─────────────────────────────────────────────

class ArtikelForm(forms.ModelForm):
    class Meta:
        model = Artikel
        fields = [
            'bezeichnung', 'beschreibung',
            'einheit', 'einzelpreis', 'steuersatz',
            'aktiv',
        ]
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 2}),
            'einzelpreis':  forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Bruttopreis inkl. MwSt.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['steuersatz'].initial = 19.00


# ─────────────────────────────────────────────
#  ANGEBOT
# ─────────────────────────────────────────────

class AngebotForm(forms.ModelForm):
    class Meta:
        model = Angebot
        fields = [
            'kunde', 'datum', 'gueltig_bis',
            'status', 'betreff',
            'einleitungstext', 'schlusstext',
            'interne_notizen',
        ]
        widgets = {
            'datum':            forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'gueltig_bis':      forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'einleitungstext':  forms.Textarea(attrs={'rows': 3}),
            'schlusstext':      forms.Textarea(attrs={'rows': 3}),
            'interne_notizen':  forms.Textarea(attrs={'rows': 2}),
        }


class AngebotPositionForm(forms.ModelForm):
    # Optionales Feld: Artikel aus Stamm übernehmen
    artikel = forms.ModelChoiceField(
        queryset=Artikel.objects.filter(aktiv=True),
        required=False,
        label='Aus Artikelstamm',
        help_text='Optional: Artikel auswählen um Felder automatisch zu befüllen'
    )

    class Meta:
        model = AngebotPosition
        fields = [
            'reihenfolge', 'bezeichnung', 'beschreibung',
            'menge', 'einheit', 'einzelpreis', 'steuersatz',
        ]
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 2}),
            'reihenfolge':  forms.NumberInput(attrs={'style': 'width: 60px'}),
            'menge':        forms.TextInput(attrs={'inputmode': 'decimal'}),
            'einzelpreis':  forms.TextInput(attrs={'inputmode': 'decimal'}),
            'steuersatz':   forms.TextInput(attrs={'inputmode': 'numeric'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # Standardwerte für neue Positionen
            self.fields['einheit'].initial = 'pauschal'
            self.fields['steuersatz'].initial = 19
            self.fields['reihenfolge'].initial = 1
        else:
            # Bestehende Werte mit Komma als Dezimaltrennzeichen anzeigen
            def de(val):
                if val is None:
                    return ''
                return '{:.2f}'.format(float(val)).replace('.', ',')
            def de_steuer(val):
                if val is None:
                    return ''
                f = float(val)
                return str(int(f)) if f == int(f) else str(f).replace('.', ',')
            self.initial['menge']       = de(self.instance.menge)
            self.initial['einzelpreis'] = de(self.instance.einzelpreis)
            self.initial['steuersatz']  = de_steuer(self.instance.steuersatz)

    def _dezimal(self, feldname):
        val = self.cleaned_data.get(feldname)
        if val is None:
            return val
        if isinstance(val, str):
            val = val.strip()
            # Deutsches Format: Punkt als Tausendertrenner, Komma als Dezimal
            # z.B. "1.554,63" → "1554.63", "19" → "19"
            if ',' in val:
                val = val.replace('.', '').replace(',', '.')
            try:
                from decimal import Decimal
                return Decimal(val)
            except Exception:
                raise forms.ValidationError('Ungültiger Wert.')
        return val

    def clean_menge(self):
        return self._dezimal('menge')

    def clean_einzelpreis(self):
        return self._dezimal('einzelpreis')

    def clean_steuersatz(self):
        return self._dezimal('steuersatz')


# FormSet: mehrere Positionen gleichzeitig bearbeiten
AngebotPositionFormSet = inlineformset_factory(
    Angebot,
    AngebotPosition,
    form=AngebotPositionForm,
    extra=0,
    can_delete=True
)


# ─────────────────────────────────────────────
#  RECHNUNG
# ─────────────────────────────────────────────

class RechnungForm(forms.ModelForm):
    class Meta:
        model = Rechnung
        fields = [
            'kunde', 'datum', 'faellig_am',
            'status', 'betreff',
            'einleitungstext', 'schlusstext',
            'zahlungsbedingungen', 'interne_notizen',
        ]
        widgets = {
            'datum':                forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'faellig_am':           forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'einleitungstext':      forms.Textarea(attrs={'rows': 3}),
            'schlusstext':          forms.Textarea(attrs={'rows': 3}),
            'zahlungsbedingungen':  forms.Textarea(attrs={'rows': 2}),
            'interne_notizen':      forms.Textarea(attrs={'rows': 2}),
        }


class ZahlungseingangForm(forms.Form):
    bezahlt_am     = forms.DateField(
        label='Zahlungsdatum',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    bezahlt_betrag = forms.DecimalField(
        label='Höhe des Zahlungseingangs (€)',
        max_digits=10, decimal_places=2,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'inputmode': 'decimal', 'placeholder': '0,00'}),
    )


class RechnungPositionForm(forms.ModelForm):
    # Optionales Feld: Artikel aus Stamm übernehmen
    artikel = forms.ModelChoiceField(
        queryset=Artikel.objects.filter(aktiv=True),
        required=False,
        label='Aus Artikelstamm',
        help_text='Optional: Artikel auswählen um Felder automatisch zu befüllen'
    )

    class Meta:
        model = RechnungPosition
        fields = [
            'reihenfolge', 'bezeichnung', 'beschreibung',
            'menge', 'einheit', 'einzelpreis', 'steuersatz',
        ]
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 2}),
            'reihenfolge':  forms.NumberInput(attrs={'style': 'width: 60px'}),
            'menge':        forms.NumberInput(attrs={'step': '0.01'}),
            'einzelpreis':  forms.NumberInput(attrs={'step': '0.01'}),
            'steuersatz':   forms.NumberInput(attrs={'step': '0.01'}),
        }


# FormSet: mehrere Positionen gleichzeitig bearbeiten
RechnungPositionFormSet = inlineformset_factory(
    Rechnung,
    RechnungPosition,
    form=RechnungPositionForm,
    extra=3,        # 3 leere Zeilen standardmäßig anzeigen
    can_delete=True # Positionen können gelöscht werden
)


# ─────────────────────────────────────────────
#  GUTSCHRIFT
# ─────────────────────────────────────────────

from .models import Gutschrift, GutschriftPosition

class GutschriftForm(forms.ModelForm):
    class Meta:
        model = Gutschrift
        fields = [
            'kunde', 'datum', 'rechnung',
            'status', 'betreff',
            'einleitungstext', 'schlusstext',
            'interne_notizen',
        ]
        widgets = {
            'datum':            forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'einleitungstext':  forms.Textarea(attrs={'rows': 3}),
            'schlusstext':      forms.Textarea(attrs={'rows': 3}),
            'interne_notizen':  forms.Textarea(attrs={'rows': 2}),
        }


class GutschriftPositionForm(forms.ModelForm):
    artikel = forms.ModelChoiceField(
        queryset=Artikel.objects.filter(aktiv=True),
        required=False,
        label='Aus Artikelstamm',
    )

    class Meta:
        model = GutschriftPosition
        fields = [
            'reihenfolge', 'bezeichnung', 'beschreibung',
            'menge', 'einheit', 'einzelpreis', 'steuersatz',
        ]
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 2}),
            'reihenfolge':  forms.NumberInput(attrs={'style': 'width: 60px'}),
            'menge':        forms.NumberInput(attrs={'step': '0.01'}),
            'einzelpreis':  forms.NumberInput(attrs={'step': '0.01'}),
            'steuersatz':   forms.NumberInput(attrs={'step': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['einheit'].initial = 'pauschal'
            self.fields['steuersatz'].initial = 19
            self.fields['reihenfolge'].initial = 1


GutschriftPositionFormSet = inlineformset_factory(
    Gutschrift,
    GutschriftPosition,
    form=GutschriftPositionForm,
    extra=1,
    can_delete=True
)
