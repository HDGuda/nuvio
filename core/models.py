from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
import datetime
from decimal import Decimal, ROUND_HALF_UP


# ─────────────────────────────────────────────
#  SUMMENBERECHNUNG (gemeinsam für Angebot, Rechnung, Gutschrift)
# ─────────────────────────────────────────────

CENT = Decimal('0.01')


def steuergruppen_berechnen(positionen, kleinunternehmer=False):
    """
    Gruppiert Positionen nach Steuersatz (absteigend) und liefert je Satz
    {'satz', 'brutto', 'netto', 'mwst'}.

    Preise werden in nuvio brutto erfasst. Deshalb wird je Steuersatz die
    Brutto-Summe gebildet und daraus Netto und Steuer herausgerechnet
    (einmal gerundet, nicht je Position). Die Steuer ist die Differenz,
    dadurch gilt immer netto + mwst == brutto, und der Bruttobetrag bleibt
    exakt der erfasste Betrag.

    Kleinunternehmer (§ 19 UStG): Es wird keine Umsatzsteuer berechnet, alle
    Positionen zählen mit Steuersatz 0. Der erfasste Preis ist der
    Rechnungsbetrag, netto == brutto und mwst == 0.
    """
    brutto_je_satz = {}
    for p in positionen:
        satz = Decimal('0') if kleinunternehmer else Decimal(str(p.steuersatz))
        brutto_je_satz[satz] = brutto_je_satz.get(satz, Decimal('0')) + p.gesamtpreis_brutto

    gruppen = []
    for satz in sorted(brutto_je_satz, reverse=True):
        brutto = brutto_je_satz[satz]
        netto = (brutto / (1 + satz / 100)).quantize(CENT, rounding=ROUND_HALF_UP)
        gruppen.append({
            'satz':   satz,
            'brutto': brutto,
            'netto':  netto,
            'mwst':   brutto - netto,
        })
    return gruppen


class SummenMixin:
    """
    Gemeinsame Summenberechnung für Angebot, Rechnung und Gutschrift
    (erwartet die Relation `positionen` mit gesamtpreis_brutto und steuersatz
    sowie das Feld `kleinunternehmer`, das beim Anlegen des Dokuments aus den
    Einstellungen festgehalten wird).
    """

    @property
    def steuergruppen(self):
        return steuergruppen_berechnen(
            self.positionen.all(),
            kleinunternehmer=self.kleinunternehmer,
        )

    @property
    def netto(self):
        return sum((g['netto'] for g in self.steuergruppen), Decimal('0.00'))

    @property
    def mwst_gesamt(self):
        return sum((g['mwst'] for g in self.steuergruppen), Decimal('0.00'))

    @property
    def brutto(self):
        return sum((g['brutto'] for g in self.steuergruppen), Decimal('0.00'))


# ─────────────────────────────────────────────
#  EINSTELLUNGEN (Singleton)
# ─────────────────────────────────────────────

class Einstellungen(models.Model):
    # Firmendaten
    firma_name              = models.CharField(max_length=200, verbose_name='Firmenname')
    firma_zusatz            = models.CharField(max_length=200, blank=True, verbose_name='Zusatz')
    firma_zusatz2           = models.CharField(max_length=200, blank=True, verbose_name='Zusatz 2')
    strasse                 = models.CharField(max_length=200, verbose_name='Straße')
    plz                     = models.CharField(max_length=10, verbose_name='PLZ')
    ort                     = models.CharField(max_length=100, verbose_name='Ort')
    telefon                 = models.CharField(max_length=50, blank=True, verbose_name='Telefon')
    email                   = models.EmailField(blank=True, verbose_name='E-Mail')
    website                 = models.URLField(blank=True, verbose_name='Website')
    logo                    = models.ImageField(upload_to='logo/', blank=True, verbose_name='Logo')
    hintergrund_pdf         = models.FileField(upload_to='hintergrund/', blank=True, null=True, verbose_name='Hintergrund-PDF')

    # Steuer
    steuernummer            = models.CharField(max_length=50, blank=True, verbose_name='Steuernummer')
    ust_id                  = models.CharField(max_length=50, blank=True, verbose_name='USt-IdNr.')
    kleinunternehmer        = models.BooleanField(
                                default=False,
                                verbose_name='Kleinunternehmer (§ 19 UStG)',
                                help_text='Aktiv: Es wird keine Umsatzsteuer berechnet oder ausgewiesen. '
                                          'Auf Angeboten, Rechnungen und Gutschriften erscheint der Kleinunternehmer-Hinweis.'
                              )

    # Bankverbindung
    bank_name               = models.CharField(max_length=100, blank=True, verbose_name='Bank')
    iban                    = models.CharField(max_length=50, blank=True, verbose_name='IBAN')
    bic                     = models.CharField(max_length=20, blank=True, verbose_name='BIC')

    # Nummernkreise Angebote
    angebot_prefix          = models.CharField(max_length=10, default='AN', verbose_name='Angebot-Präfix')
    angebot_naechste_nummer = models.IntegerField(default=1, verbose_name='Nächste Angebotsnummer')
    angebot_format          = models.CharField(
                                max_length=50,
                                default='{prefix}-{jahr}-{nummer:04d}',
                                verbose_name='Angebot-Format',
                                help_text='Platzhalter: {prefix}, {jahr}, {nummer:04d} → z.B. AN-2026-0001'
                              )

    # Nummernkreise Rechnungen
    rechnung_prefix          = models.CharField(max_length=10, default='RE', verbose_name='Rechnung-Präfix')
    rechnung_naechste_nummer = models.IntegerField(default=1, verbose_name='Nächste Rechnungsnummer')
    rechnung_format          = models.CharField(
                                max_length=50,
                                default='{prefix}-{jahr}-{nummer:04d}',
                                verbose_name='Rechnung-Format',
                                help_text='Platzhalter: {prefix}, {jahr}, {nummer:04d} → z.B. RE-2026-0001'
                               )

    # Nummernkreise Gutschriften
    gutschrift_prefix          = models.CharField(max_length=10, default='GS', verbose_name='Gutschrift-Präfix')
    gutschrift_naechste_nummer = models.IntegerField(default=1, verbose_name='Nächste Gutschriftnummer')
    gutschrift_format          = models.CharField(
                                max_length=50,
                                default='{prefix}-{jahr}-{nummer:04d}',
                                verbose_name='Gutschrift-Format',
                              )

    # Standardtexte
    angebot_einleitung      = models.TextField(blank=True, verbose_name='Angebot Einleitungstext')
    angebot_schlusstext     = models.TextField(blank=True, verbose_name='Angebot Schlusstext')
    rechnung_einleitung     = models.TextField(blank=True, verbose_name='Rechnung Einleitungstext')
    rechnung_schlusstext    = models.TextField(blank=True, verbose_name='Rechnung Schlusstext')
    zahlungsbedingungen     = models.TextField(
                                blank=True,
                                default='Zahlbar innerhalb von 14 Tagen ohne Abzug.',
                                verbose_name='Zahlungsbedingungen'
                              )

    # ── E-MAIL-VORLAGEN ANGEBOT ──
    email_angebot_betreff   = models.CharField(
                                max_length=200, blank=True,
                                default='Angebot {{nummer}} – {{firma}}',
                                verbose_name='Betreff-Vorlage Angebot',
                                help_text='Platzhalter: {{nummer}}, {{kundenname}}, {{firma}}, {{datum}}'
                              )
    email_angebot_text      = models.TextField(
                                blank=True,
                                verbose_name='E-Mail-Text Angebot',
                              )
    email_angebot_anhang1   = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 1 (Angebot)',
                              )
    email_angebot_anhang2   = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 2 (Angebot)',
                              )

    # ── E-Mail-Vorlage: Rechnungen ──
    email_rechnung_betreff  = models.CharField(
                                max_length=200, blank=True,
                                default='Rechnung {{nummer}} – {{firma}}',
                                verbose_name='Betreff-Vorlage Rechnung',
                                help_text='Platzhalter: {{nummer}}, {{kundenname}}, {{firma}}, {{datum}}',
                              )
    email_rechnung_text     = models.TextField(
                                blank=True,
                                verbose_name='E-Mail-Text Rechnung',
                              )
    email_rechnung_anhang1  = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 1 (Rechnung)',
                              )
    email_rechnung_anhang2  = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 2 (Rechnung)',
                              )

    # ── E-Mail-Vorlage: Gutschriften ──
    email_gutschrift_betreff = models.CharField(
                                max_length=200, blank=True,
                                default='Gutschrift {{nummer}} – {{firma}}',
                                verbose_name='Betreff-Vorlage Gutschrift',
                                help_text='Platzhalter: {{nummer}}, {{kundenname}}, {{firma}}, {{datum}}',
                              )
    email_gutschrift_text    = models.TextField(
                                blank=True,
                                verbose_name='E-Mail-Text Gutschrift',
                              )
    email_gutschrift_anhang1 = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 1 (Gutschrift)',
                              )
    email_gutschrift_anhang2 = models.FileField(
                                upload_to='email_anhaenge/', blank=True, null=True,
                                verbose_name='Standard-Anhang 2 (Gutschrift)',
                              )

    class Meta:
        verbose_name = 'Einstellungen'

    def __str__(self):
        return 'Einstellungen'

    def save(self, *args, **kwargs):
        # Singleton: immer nur ein Datensatz mit pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def laden(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def naechste_angebotsnummer(self):
        nummer = self.angebot_format.format(
            prefix=self.angebot_prefix,
            jahr=datetime.date.today().strftime('%y'),
            nummer=self.angebot_naechste_nummer
        )
        self.angebot_naechste_nummer += 1
        self.save()
        return nummer

    def naechste_gutschriftnummer(self):
        nummer = self.gutschrift_format.format(
            prefix=self.gutschrift_prefix,
            jahr=datetime.date.today().strftime('%y'),
            nummer=self.gutschrift_naechste_nummer
        )
        self.gutschrift_naechste_nummer += 1
        self.save()
        return nummer

    def naechste_rechnungsnummer(self):
        nummer = self.rechnung_format.format(
            prefix=self.rechnung_prefix,
            jahr=datetime.date.today().strftime('%y'),
            nummer=self.rechnung_naechste_nummer
        )
        self.rechnung_naechste_nummer += 1
        self.save()
        return nummer


# ─────────────────────────────────────────────
#  ABSENDERPROFIL (Darstellung je Rolle, KEIN Mandant)
# ─────────────────────────────────────────────

class RechnungGesperrt(Exception):
    """Wird ausgelöst, wenn eine bezahlte (gesperrte) Rechnung geändert werden soll."""


class Absenderprofil(models.Model):
    """
    Darstellungsprofil für den Aussteller, z. B. "Energieberatung",
    "Unternehmensberatung", "Redaktion": Briefpapier, Logo, Kopfblöcke und
    Absenderzeile. Nummernkreise, Steuerdaten, Bank und der
    Kleinunternehmer-Schalter bleiben global in den Einstellungen.
    """
    LOGO_POSITION_CHOICES = [
        ('links',  'Links'),
        ('rechts', 'Rechts'),
    ]

    name            = models.CharField(max_length=100, unique=True, verbose_name='Bezeichnung (intern)')
    ist_standard    = models.BooleanField(default=False, verbose_name='Standardprofil',
                                          help_text='Wird bei neuen Rechnungen vorausgewählt. Es gibt genau ein Standardprofil.')
    firmenname      = models.CharField(max_length=200, blank=True, verbose_name='Firmenname im Dokument',
                                       help_text='Fettgedruckt im Briefkopf und Platzhalter {{firma}} in E-Mails. '
                                                 'Leer = Firmenname aus den Einstellungen.')
    logo            = models.ImageField(upload_to='logo/', blank=True, verbose_name='Logo')
    logo_position   = models.CharField(max_length=10, choices=LOGO_POSITION_CHOICES, default='rechts',
                                       verbose_name='Logo-Position')
    kopf_links      = models.TextField(blank=True, verbose_name='Briefkopf links',
                                       help_text='Mehrzeilig, z. B. Zusatzzeilen, Straße, Ort, E-Mail.')
    kopf_rechts     = models.TextField(blank=True, verbose_name='Briefkopf rechts',
                                       help_text='Mehrzeilig, rechtsbündig. Darf leer sein.')
    absenderzeile   = models.CharField(max_length=200, blank=True, verbose_name='Absenderzeile über der Empfängeradresse',
                                       help_text='Kleine Zeile im Adressfenster, z. B. "Name · Straße · PLZ Ort".')
    hintergrund_pdf = models.FileField(upload_to='hintergrund/', blank=True, null=True, verbose_name='Hintergrund-PDF (Briefpapier)')
    thunderbird_identitaet = models.CharField(
        max_length=10, blank=True,
        validators=[RegexValidator(r'^id\d+$', 'Bitte in der Form id1, id2, id3 … angeben.')],
        verbose_name='Thunderbird-Identität',
        help_text='Nummer der Absender-Identität in Thunderbird, z. B. id2. Leer = Standard-Identität.',
    )
    unterer_rand_mm = models.PositiveSmallIntegerField(default=28, verbose_name='Unterer Seitenrand mit Briefpapier (mm)',
                                                       help_text='Muss zur Fußzeile des Briefpapiers passen.')

    class Meta:
        verbose_name = 'Absenderprofil'
        verbose_name_plural = 'Absenderprofile'
        ordering = ['-ist_standard', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.ist_standard:
            # genau ein Standardprofil
            Absenderprofil.objects.exclude(pk=self.pk).filter(ist_standard=True).update(ist_standard=False)

    @property
    def firma_anzeige(self):
        return self.firmenname or Einstellungen.laden().firma_name

    @classmethod
    def aus_einstellungen(cls):
        """Legt das Profil "Standard" aus den bisherigen Firmendaten der Einstellungen an."""
        e = Einstellungen.laden()
        ort_zeile = f'{e.plz} {e.ort}'.strip()
        kopf = '\n'.join(z for z in [e.firma_zusatz, e.firma_zusatz2, e.strasse, ort_zeile, e.email] if z)
        absender = ' · '.join(t for t in [e.firma_name, e.strasse, ort_zeile] if t)
        return cls.objects.create(
            name='Standard',
            ist_standard=True,
            firmenname=e.firma_name,
            logo=e.logo.name if e.logo else '',
            logo_position='rechts',
            kopf_links=kopf,
            absenderzeile=absender,
            hintergrund_pdf=e.hintergrund_pdf.name if e.hintergrund_pdf else None,
        )

    @classmethod
    def standard(cls):
        """Standardprofil; legt es bei Bedarf aus den Einstellungen an."""
        return (cls.objects.filter(ist_standard=True).first()
                or cls.objects.first()
                or cls.aus_einstellungen())


# ─────────────────────────────────────────────
#  KUNDE
# ─────────────────────────────────────────────

class Kunde(models.Model):
    # Basisdaten
    firma                   = models.CharField(max_length=200, blank=True, verbose_name='Firma')
    nachname                = models.CharField(max_length=100, verbose_name='Nachname')
    vorname                 = models.CharField(max_length=100, blank=True, verbose_name='Vorname')
    strasse                 = models.CharField(max_length=200, verbose_name='Straße')
    plz                     = models.CharField(max_length=10, verbose_name='PLZ')
    ort                     = models.CharField(max_length=100, verbose_name='Ort')
    land                    = models.CharField(max_length=100, default='Deutschland', verbose_name='Land')

    # Kontakt
    email                   = models.EmailField(blank=True, verbose_name='E-Mail')
    telefon                 = models.CharField(max_length=50, blank=True, verbose_name='Telefon')
    website                 = models.URLField(blank=True, verbose_name='Website')

    # Steuer
    ust_id                  = models.CharField(max_length=50, blank=True, verbose_name='USt-IdNr.')

    # Metadaten
    notizen                 = models.TextField(blank=True, verbose_name='Notizen')
    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kunde'
        verbose_name_plural = 'Kunden'
        ordering = ['firma', 'nachname', 'vorname']

    def __str__(self):
        if self.firma:
            return self.firma
        name = self.nachname
        if self.vorname:
            name = f'{self.nachname}, {self.vorname}'
        return name or f'Kunde #{self.pk}'

    @property
    def ansprechpartner(self):
        """Vollständiger Name (Vorname Nachname) – für Templates und PDFs."""
        teile = [t for t in [self.vorname, self.nachname] if t]
        return ' '.join(teile)

    @property
    def anzeigename(self):
        """Listenansicht: 'Nachname, Vorname' oder Firma."""
        if self.firma:
            return self.firma
        if self.vorname:
            return f'{self.nachname}, {self.vorname}'
        return self.nachname or f'Kunde #{self.pk}'


# ─────────────────────────────────────────────
#  ARTIKEL (Artikelstamm)
# ─────────────────────────────────────────────

class Artikel(models.Model):
    STEUER_CHOICES = [
        (0.00,  '0 % (steuerfrei)'),
        (7.00,  '7 % (ermäßigt)'),
        (19.00, '19 % (Regelsteuersatz)'),
    ]

    bezeichnung             = models.CharField(max_length=200, verbose_name='Bezeichnung')
    beschreibung            = models.TextField(blank=True, verbose_name='Beschreibung')
    einheit                 = models.CharField(
                                max_length=50,
                                default='Std.',
                                verbose_name='Einheit',
                                help_text='z.B. Std., Stk., pauschal'
                              )
    einzelpreis             = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Einzelpreis (€)')
    steuersatz              = models.DecimalField(
                                max_digits=5,
                                decimal_places=2,
                                choices=STEUER_CHOICES,
                                default=19.00,
                                verbose_name='Steuersatz'
                              )
    aktiv                   = models.BooleanField(default=True, verbose_name='Aktiv')
    is_bundle               = models.BooleanField(
                                default=False,
                                verbose_name='Bundle (Paketartikel)',
                                help_text='Wenn aktiv, werden beim Einfügen in ein Angebot automatisch '
                                          'alle Einzelartikel dieses Bundles eingefügt.'
                              )

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['bezeichnung']

    def __str__(self):
        return f'{self.bezeichnung} ({self.einzelpreis} €)'


# ─────────────────────────────────────────────
#  ARTIKEL-BUNDLE-POSITIONEN
# ─────────────────────────────────────────────

class ArtikelBundlePosition(models.Model):
    bundle      = models.ForeignKey(
                    Artikel,
                    on_delete=models.CASCADE,
                    related_name='bundle_positionen',
                    verbose_name='Bundle-Artikel'
                  )
    artikel     = models.ForeignKey(
                    Artikel,
                    on_delete=models.CASCADE,
                    related_name='in_bundles',
                    limit_choices_to={'aktiv': True, 'is_bundle': False},
                    verbose_name='Einzelartikel'
                  )
    menge       = models.DecimalField(
                    max_digits=10, decimal_places=2,
                    default=1,
                    verbose_name='Menge'
                  )
    reihenfolge = models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')

    class Meta:
        verbose_name        = 'Bundle-Position'
        verbose_name_plural = 'Bundle-Positionen'
        ordering            = ['reihenfolge']

    def __str__(self):
        return f'{self.menge} × {self.artikel.bezeichnung}'


# ─────────────────────────────────────────────
#  VORLAGE
# ─────────────────────────────────────────────

class Vorlage(models.Model):
    TYP_CHOICES = [
        ('angebot',  'Angebot'),
        ('rechnung', 'Rechnung'),
    ]

    name                    = models.CharField(max_length=100, verbose_name='Name')
    typ                     = models.CharField(max_length=20, choices=TYP_CHOICES, verbose_name='Typ')
    html_inhalt             = models.TextField(verbose_name='HTML-Inhalt')
    ist_standard            = models.BooleanField(default=False, verbose_name='Standardvorlage')
    erstellt_am             = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vorlage'
        verbose_name_plural = 'Vorlagen'

    def __str__(self):
        return f'{self.name} ({self.get_typ_display()})'

    def save(self, *args, **kwargs):
        # Wenn diese Vorlage als Standard gesetzt wird,
        # alle anderen des gleichen Typs auf nicht-Standard setzen
        if self.ist_standard:
            Vorlage.objects.filter(typ=self.typ, ist_standard=True).update(ist_standard=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
#  ANGEBOT
# ─────────────────────────────────────────────

class Angebot(SummenMixin, models.Model):
    STATUS_CHOICES = [
        ('entwurf',    'Entwurf'),
        ('gesendet',   'Gesendet'),
        ('angenommen', 'Angenommen'),
        ('abgelehnt',  'Abgelehnt'),
        ('abgelaufen', 'Abgelaufen'),
    ]

    # Kopfdaten
    nummer                  = models.CharField(max_length=50, unique=True, verbose_name='Angebotsnummer')
    kunde                   = models.ForeignKey(Kunde, on_delete=models.PROTECT, verbose_name='Kunde')
    datum                   = models.DateField(default=timezone.now, verbose_name='Datum')
    gueltig_bis             = models.DateField(null=True, blank=True, verbose_name='Gültig bis')
    status                  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entwurf', verbose_name='Status')
    betreff                 = models.CharField(max_length=300, blank=True, verbose_name='Betreff')

    # Texte (manuell veränderbar)
    einleitungstext         = models.TextField(blank=True, verbose_name='Einleitungstext')
    schlusstext             = models.TextField(blank=True, verbose_name='Schlusstext')
    interne_notizen         = models.TextField(blank=True, verbose_name='Interne Notizen (erscheint nicht im PDF)')

    # Vorlage
    vorlage                 = models.ForeignKey(
                                Vorlage,
                                null=True, blank=True,
                                on_delete=models.SET_NULL,
                                verbose_name='Vorlage'
                              )

    # Kleinunternehmer-Status: wird beim Anlegen aus den Einstellungen festgehalten
    # und ändert sich danach nicht mehr (spätere Umstellung wirkt nur auf neue Dokumente)
    kleinunternehmer        = models.BooleanField(
                                default=False, editable=False,
                                verbose_name='Kleinunternehmer (§ 19 UStG) bei Erstellung'
                              )

    # Darstellungsprofil (Briefpapier, Logo, Kopfblöcke); wird bei der Rechnung übernommen
    absenderprofil          = models.ForeignKey(
                                Absenderprofil,
                                null=True, blank=True,
                                on_delete=models.PROTECT,
                                related_name='angebote',
                                verbose_name='Absenderprofil'
                              )

    # Metadaten
    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)
    gesendet_am             = models.DateField(null=True, blank=True, verbose_name='Gesendet am')

    class Meta:
        verbose_name = 'Angebot'
        verbose_name_plural = 'Angebote'
        ordering = ['-datum', '-nummer']

    def __str__(self):
        return f'{self.nummer} – {self.kunde}'

    @property
    def profil(self):
        """Absenderprofil des Angebots; Angebote ohne Zuordnung nutzen das Standardprofil."""
        return self.absenderprofil or Absenderprofil.standard()

    def save(self, *args, **kwargs):
        # Kleinunternehmer-Status und Absenderprofil beim Anlegen festhalten
        if self._state.adding:
            self.kleinunternehmer = Einstellungen.laden().kleinunternehmer
            if not self.absenderprofil_id:
                self.absenderprofil = Absenderprofil.standard()
        # Automatische Nummernvergabe beim ersten Speichern
        if not self.nummer:
            self.nummer = Einstellungen.laden().naechste_angebotsnummer()
        # Standardtexte aus Einstellungen übernehmen, falls leer
        if not self.einleitungstext:
            self.einleitungstext = Einstellungen.laden().angebot_einleitung
        if not self.schlusstext:
            self.schlusstext = Einstellungen.laden().angebot_schlusstext
        super().save(*args, **kwargs)

    # ── Berechnungen ──

    def in_rechnung_umwandeln(self):
        """Erstellt eine neue Rechnung auf Basis dieses Angebots."""
        rechnung = Rechnung(
            kunde           = self.kunde,
            betreff         = self.betreff,
            einleitungstext = self.einleitungstext,
            schlusstext     = self.schlusstext,
            absenderprofil  = self.profil,
            angebot         = self,
        )
        rechnung.save()
        for position in self.positionen.all():
            RechnungPosition.objects.create(
                rechnung      = rechnung,
                bezeichnung   = position.bezeichnung,
                beschreibung  = position.beschreibung,
                menge         = position.menge,
                einheit       = position.einheit,
                einzelpreis   = position.einzelpreis,
                steuersatz    = position.steuersatz,
            )
        self.status = 'angenommen'
        self.save()
        return rechnung


# ─────────────────────────────────────────────
#  ANGEBOT-POSITION
# ─────────────────────────────────────────────

class AngebotPosition(models.Model):
    angebot                 = models.ForeignKey(Angebot, on_delete=models.CASCADE, related_name='positionen')
    reihenfolge             = models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')

    bezeichnung             = models.CharField(max_length=200, verbose_name='Bezeichnung')
    beschreibung            = models.TextField(blank=True, verbose_name='Beschreibung')
    menge                   = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='Menge')
    einheit                 = models.CharField(max_length=50, default='Std.', verbose_name='Einheit')
    einzelpreis             = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Einzelpreis inkl. MwSt. (€)')
    steuersatz              = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, verbose_name='Steuersatz (%)')

    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positionen'
        ordering = ['reihenfolge']

    def __str__(self):
        return f'{self.bezeichnung} ({self.menge} × {self.einzelpreis} €)'

    @property
    def einzelpreis_netto(self):
        """Nettopreis aus Bruttopreis herausrechnen"""
        return round(self.einzelpreis / (1 + self.steuersatz / 100), 2)

    @property
    def gesamtpreis_netto(self):
        return round(self.menge * self.einzelpreis_netto, 2)

    @property
    def mwst_betrag(self):
        return round(self.gesamtpreis_netto * self.steuersatz / 100, 2)

    @property
    def gesamtpreis_brutto(self):
        return round(self.menge * self.einzelpreis, 2)


# ─────────────────────────────────────────────
#  RECHNUNG
# ─────────────────────────────────────────────

class Rechnung(SummenMixin, models.Model):
    STATUS_CHOICES = [
        ('entwurf',   'Entwurf'),
        ('gesendet',  'Gesendet'),
        ('bezahlt',      'Bezahlt'),
        ('teilbezahlt',   'Teilbezahlt'),
        ('ueberfaellig',  'Überfällig'),
        ('storniert',          'Storniert'),
        ('teilgutgeschrieben', 'Teilgutgeschrieben'),
    ]

    # Kopfdaten
    nummer                  = models.CharField(max_length=50, unique=True, verbose_name='Rechnungsnummer')
    kunde                   = models.ForeignKey(Kunde, on_delete=models.PROTECT, verbose_name='Kunde')
    datum                   = models.DateField(default=timezone.now, verbose_name='Datum')
    faellig_am              = models.DateField(null=True, blank=True, verbose_name='Fällig am')
    status                  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entwurf', verbose_name='Status')
    betreff                 = models.CharField(max_length=300, blank=True, verbose_name='Betreff')
    angebot                 = models.ForeignKey(
                                Angebot,
                                null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='rechnungen',
                                verbose_name='Ursprungsangebot'
                              )

    # Texte
    einleitungstext         = models.TextField(blank=True, verbose_name='Einleitungstext')
    schlusstext             = models.TextField(blank=True, verbose_name='Schlusstext')
    zahlungsbedingungen     = models.TextField(blank=True, verbose_name='Zahlungsbedingungen')
    interne_notizen         = models.TextField(blank=True, verbose_name='Interne Notizen')

    # Kleinunternehmer-Status: wird beim Anlegen aus den Einstellungen festgehalten
    # und ändert sich danach nicht mehr (spätere Umstellung wirkt nur auf neue Dokumente)
    kleinunternehmer        = models.BooleanField(
                                default=False, editable=False,
                                verbose_name='Kleinunternehmer (§ 19 UStG) bei Erstellung'
                              )

    # Darstellungsprofil (Briefpapier, Logo, Kopfblöcke); gleicher Nummernkreis für alle Profile
    absenderprofil          = models.ForeignKey(
                                Absenderprofil,
                                null=True, blank=True,
                                on_delete=models.PROTECT,
                                related_name='rechnungen',
                                verbose_name='Absenderprofil'
                              )

    # GoBD: Ab "Bezahlt" ist die Rechnung unveränderbar. gesperrt_am wird einmalig
    # gesetzt und nie zurückgenommen (der Status kann sich durch Gutschriften ändern).
    gesperrt_am             = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Gesperrt am')
    pdf_archiv              = models.FileField(
                                upload_to='rechnungen_archiv/', null=True, blank=True, editable=False,
                                verbose_name='Archiviertes PDF'
                              )

    # Metadaten
    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)
    gesendet_am             = models.DateField(null=True, blank=True, verbose_name='Gesendet am')

    # Felder, die auch bei einer gesperrten Rechnung geschrieben werden dürfen
    SPERRE_ERLAUBT = {'status', 'gesendet_am', 'interne_notizen', 'gesperrt_am', 'pdf_archiv', 'geaendert_am'}

    class Meta:
        verbose_name = 'Rechnung'
        verbose_name_plural = 'Rechnungen'
        ordering = ['-datum', '-nummer']

    def __str__(self):
        return f'{self.nummer} – {self.kunde}'

    def save(self, *args, **kwargs):
        # GoBD-Sperre: eine bezahlte Rechnung darf nur noch Status, Notizen und
        # Archiv-Felder ändern (z. B. Statuswechsel durch Gutschriften)
        if self.ist_gesperrt and not self._state.adding:
            felder = kwargs.get('update_fields')
            if felder is None or not set(felder) <= self.SPERRE_ERLAUBT:
                raise RechnungGesperrt(f'Rechnung {self.nummer} ist bezahlt und gesperrt.')
        # Kleinunternehmer-Status und Absenderprofil beim Anlegen festhalten
        if self._state.adding:
            self.kleinunternehmer = Einstellungen.laden().kleinunternehmer
            if not self.absenderprofil_id:
                self.absenderprofil = Absenderprofil.standard()
        if not self.nummer:
            self.nummer = Einstellungen.laden().naechste_rechnungsnummer()
        if not self.einleitungstext:
            self.einleitungstext = Einstellungen.laden().rechnung_einleitung
        if not self.schlusstext:
            self.schlusstext = Einstellungen.laden().rechnung_schlusstext
        if not self.zahlungsbedingungen:
            self.zahlungsbedingungen = Einstellungen.laden().zahlungsbedingungen
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ist_gesperrt:
            raise RechnungGesperrt(f'Rechnung {self.nummer} ist bezahlt und gesperrt.')
        return super().delete(*args, **kwargs)

    @property
    def ist_gesperrt(self):
        return self.gesperrt_am is not None

    @property
    def profil(self):
        """Absenderprofil der Rechnung; Rechnungen ohne Zuordnung nutzen das Standardprofil."""
        return self.absenderprofil or Absenderprofil.standard()

    def sperren_falls_bezahlt(self):
        """
        Setzt die dauerhafte Sperre, sobald der Status "Bezahlt" ist.
        Gibt True zurück, wenn die Rechnung dadurch neu gesperrt wurde.
        Aufruf nach dem Speichern von Rechnung UND Positionen.
        """
        if self.status == 'bezahlt' and self.gesperrt_am is None:
            self.gesperrt_am = timezone.now()
            self.save(update_fields=['gesperrt_am'])
            return True
        return False

    @property
    def bezahlt_summe(self):
        return round(sum(z.betrag for z in self.zahlungen.all()), 2)

    @property
    def gutschrift_summe(self):
        gutschriften = self.gutschriften.exclude(status='storniert')
        return round(sum(g.brutto for g in gutschriften), 2)

    @property
    def offener_betrag(self):
        return round(self.brutto - self.bezahlt_summe - self.gutschrift_summe, 2)

    def gutschrift_status_aktualisieren(self):
        gutschriften = self.gutschriften.exclude(status='storniert')
        if not gutschriften.exists():
            if self.status in ('storniert', 'teilgutgeschrieben'):
                self.status = 'bezahlt' if self.ist_gesperrt else 'gesendet'
                self.save(update_fields=['status'])
            return
        gutschrift_summe = sum(g.brutto for g in gutschriften)
        if gutschrift_summe >= self.brutto:
            self.status = 'storniert'
        else:
            self.status = 'teilgutgeschrieben'
        self.save(update_fields=['status'])


# ─────────────────────────────────────────────
#  ZAHLUNG (Teilzahlungen zu einer Rechnung)
# ─────────────────────────────────────────────

class Zahlung(models.Model):
    rechnung    = models.ForeignKey(Rechnung, on_delete=models.CASCADE, related_name='zahlungen', verbose_name='Rechnung')
    datum       = models.DateField(verbose_name='Zahlungsdatum')
    betrag      = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Betrag (€)')
    erstellt_am = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Zahlung'
        verbose_name_plural = 'Zahlungen'
        ordering = ['datum', 'erstellt_am']

    def __str__(self):
        return f'{self.betrag} € am {self.datum} zu {self.rechnung.nummer}'


# ─────────────────────────────────────────────
#  RECHNUNG-POSITION
# ─────────────────────────────────────────────

class RechnungPosition(models.Model):
    rechnung                = models.ForeignKey(Rechnung, on_delete=models.CASCADE, related_name='positionen')
    reihenfolge             = models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')

    bezeichnung             = models.CharField(max_length=200, verbose_name='Bezeichnung')
    beschreibung            = models.TextField(blank=True, verbose_name='Beschreibung')
    menge                   = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='Menge')
    einheit                 = models.CharField(max_length=50, default='Std.', verbose_name='Einheit')
    einzelpreis             = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Einzelpreis inkl. MwSt. (€)')
    steuersatz              = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, verbose_name='Steuersatz (%)')

    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positionen'
        ordering = ['reihenfolge']

    def __str__(self):
        return f'{self.bezeichnung} ({self.menge} × {self.einzelpreis} €)'

    def save(self, *args, **kwargs):
        if self.rechnung.ist_gesperrt:
            raise RechnungGesperrt(f'Rechnung {self.rechnung.nummer} ist bezahlt und gesperrt.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.rechnung.ist_gesperrt:
            raise RechnungGesperrt(f'Rechnung {self.rechnung.nummer} ist bezahlt und gesperrt.')
        return super().delete(*args, **kwargs)

    @property
    def einzelpreis_netto(self):
        """Nettopreis aus Bruttopreis herausrechnen"""
        return round(self.einzelpreis / (1 + self.steuersatz / 100), 2)

    @property
    def gesamtpreis_netto(self):
        return round(self.menge * self.einzelpreis_netto, 2)

    @property
    def mwst_betrag(self):
        return round(self.gesamtpreis_netto * self.steuersatz / 100, 2)

    @property
    def gesamtpreis_brutto(self):
        return round(self.menge * self.einzelpreis, 2)


# ─────────────────────────────────────────────
#  GUTSCHRIFT
# ─────────────────────────────────────────────

class Gutschrift(SummenMixin, models.Model):
    STATUS_CHOICES = [
        ('entwurf',   'Entwurf'),
        ('gesendet',  'Gesendet'),
        ('storniert', 'Storniert'),
    ]

    nummer                  = models.CharField(max_length=50, unique=True, verbose_name='Gutschriftnummer')
    kunde                   = models.ForeignKey(Kunde, on_delete=models.PROTECT, verbose_name='Kunde')
    datum                   = models.DateField(default=timezone.now, verbose_name='Datum')
    status                  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entwurf', verbose_name='Status')
    betreff                 = models.CharField(max_length=300, blank=True, verbose_name='Betreff')

    # Optionaler Bezug zur Rechnung
    rechnung                = models.ForeignKey(
                                Rechnung,
                                null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='gutschriften',
                                verbose_name='Zu Rechnung'
                              )

    einleitungstext         = models.TextField(blank=True, verbose_name='Einleitungstext')
    schlusstext             = models.TextField(blank=True, verbose_name='Schlusstext')
    interne_notizen         = models.TextField(blank=True, verbose_name='Interne Notizen')

    # Kleinunternehmer-Status: wird beim Anlegen aus den Einstellungen festgehalten
    # und ändert sich danach nicht mehr (spätere Umstellung wirkt nur auf neue Dokumente)
    kleinunternehmer        = models.BooleanField(
                                default=False, editable=False,
                                verbose_name='Kleinunternehmer (§ 19 UStG) bei Erstellung'
                              )

    # Darstellungsprofil: eine Gutschrift zu einer Rechnung übernimmt deren Profil
    absenderprofil          = models.ForeignKey(
                                Absenderprofil,
                                null=True, blank=True,
                                on_delete=models.PROTECT,
                                related_name='gutschriften',
                                verbose_name='Absenderprofil'
                              )

    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gutschrift'
        verbose_name_plural = 'Gutschriften'
        ordering = ['-datum', '-nummer']

    def __str__(self):
        return f'{self.nummer} – {self.kunde}'

    def save(self, *args, **kwargs):
        # Kleinunternehmer-Status beim Anlegen festhalten; eine Gutschrift zu einer
        # Rechnung übernimmt den Status der Rechnung (gleiche Steuerbehandlung)
        if self._state.adding:
            if self.rechnung_id:
                self.kleinunternehmer = self.rechnung.kleinunternehmer
            else:
                self.kleinunternehmer = Einstellungen.laden().kleinunternehmer
            if not self.absenderprofil_id:
                self.absenderprofil = self.rechnung.profil if self.rechnung_id else Absenderprofil.standard()
        if not self.nummer:
            self.nummer = Einstellungen.laden().naechste_gutschriftnummer()
        super().save(*args, **kwargs)

    @property
    def profil(self):
        """Absenderprofil der Gutschrift; ohne Zuordnung das der Rechnung bzw. das Standardprofil."""
        if self.absenderprofil_id:
            return self.absenderprofil
        return self.rechnung.profil if self.rechnung_id else Absenderprofil.standard()

    def delete(self, *args, **kwargs):
        rechnung = self.rechnung
        super().delete(*args, **kwargs)
        if rechnung:
            rechnung.gutschrift_status_aktualisieren()


# ─────────────────────────────────────────────
#  GUTSCHRIFT-POSITION
# ─────────────────────────────────────────────

class GutschriftPosition(models.Model):
    gutschrift              = models.ForeignKey(Gutschrift, on_delete=models.CASCADE, related_name='positionen')
    reihenfolge             = models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')

    bezeichnung             = models.CharField(max_length=200, verbose_name='Bezeichnung')
    beschreibung            = models.TextField(blank=True, verbose_name='Beschreibung')
    menge                   = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='Menge')
    einheit                 = models.CharField(max_length=50, default='Std.', verbose_name='Einheit')
    einzelpreis             = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Einzelpreis (€)')
    steuersatz              = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, verbose_name='Steuersatz (%)')

    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positionen'
        ordering = ['reihenfolge']

    def __str__(self):
        return f'{self.bezeichnung} ({self.menge} × {self.einzelpreis} €)'

    @property
    def einzelpreis_netto(self):
        return round(self.einzelpreis / (1 + self.steuersatz / 100), 2)

    @property
    def gesamtpreis_netto(self):
        return round(self.menge * self.einzelpreis_netto, 2)

    @property
    def mwst_betrag(self):
        return round(self.gesamtpreis_netto * self.steuersatz / 100, 2)

    @property
    def gesamtpreis_brutto(self):
        return round(self.menge * self.einzelpreis, 2)
