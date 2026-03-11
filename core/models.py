from django.db import models
from django.utils import timezone
import datetime


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
#  KUNDE
# ─────────────────────────────────────────────

class Kunde(models.Model):
    # Basisdaten
    firma                   = models.CharField(max_length=200, blank=True, verbose_name='Firma')
    ansprechpartner         = models.CharField(max_length=200, blank=True, verbose_name='Ansprechpartner')
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
        ordering = ['firma', 'ansprechpartner']

    def __str__(self):
        if self.firma and self.ansprechpartner:
            return f'{self.firma} – {self.ansprechpartner}'
        return self.firma or self.ansprechpartner or f'Kunde #{self.pk}'


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

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['bezeichnung']

    def __str__(self):
        return f'{self.bezeichnung} ({self.einzelpreis} €)'


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

class Angebot(models.Model):
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

    def save(self, *args, **kwargs):
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

    @property
    def netto(self):
        return round(sum(p.gesamtpreis_netto for p in self.positionen.all()), 2)

    @property
    def mwst_gesamt(self):
        return round(sum(p.mwst_betrag for p in self.positionen.all()), 2)

    @property
    def brutto(self):
        return round(self.netto + self.mwst_gesamt, 2)

    def in_rechnung_umwandeln(self):
        """Erstellt eine neue Rechnung auf Basis dieses Angebots."""
        rechnung = Rechnung(
            kunde           = self.kunde,
            betreff         = self.betreff,
            einleitungstext = self.einleitungstext,
            schlusstext     = self.schlusstext,
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

class Rechnung(models.Model):
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
    datum                   = models.DateField(default=timezone.now, verbose_name='Rechnungsdatum')
    faellig_am              = models.DateField(null=True, blank=True, verbose_name='Fällig am')
    bezahlt_am              = models.DateField(null=True, blank=True, verbose_name='Bezahlt am')
    bezahlt_betrag          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Bezahlter Betrag')
    status                  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entwurf', verbose_name='Status')
    betreff                 = models.CharField(max_length=300, blank=True, verbose_name='Betreff')

    # Verknüpfung mit Angebot (optional)
    angebot                 = models.ForeignKey(
                                Angebot,
                                null=True, blank=True,
                                on_delete=models.SET_NULL,
                                verbose_name='Aus Angebot erstellt'
                              )

    # Texte (manuell veränderbar)
    einleitungstext         = models.TextField(blank=True, verbose_name='Einleitungstext')
    schlusstext             = models.TextField(blank=True, verbose_name='Schlusstext')
    zahlungsbedingungen     = models.TextField(blank=True, verbose_name='Zahlungsbedingungen')
    interne_notizen         = models.TextField(blank=True, verbose_name='Interne Notizen (erscheint nicht im PDF)')

    # Vorlage
    vorlage                 = models.ForeignKey(
                                Vorlage,
                                null=True, blank=True,
                                on_delete=models.SET_NULL,
                                verbose_name='Vorlage'
                              )

    # Metadaten
    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)
    gesendet_am             = models.DateField(null=True, blank=True, verbose_name='Gesendet am')

    class Meta:
        verbose_name = 'Rechnung'
        verbose_name_plural = 'Rechnungen'
        ordering = ['-datum', '-nummer']

    def __str__(self):
        return f'{self.nummer} – {self.kunde}'

    def save(self, *args, **kwargs):
        # Automatische Nummernvergabe beim ersten Speichern
        if not self.nummer:
            self.nummer = Einstellungen.laden().naechste_rechnungsnummer()
        # Standardtexte aus Einstellungen übernehmen, falls leer
        if not self.einleitungstext:
            self.einleitungstext = Einstellungen.laden().rechnung_einleitung
        if not self.schlusstext:
            self.schlusstext = Einstellungen.laden().rechnung_schlusstext
        if not self.zahlungsbedingungen:
            self.zahlungsbedingungen = Einstellungen.laden().zahlungsbedingungen
        super().save(*args, **kwargs)

    # ── Berechnungen ──

    @property
    def netto(self):
        return round(sum(p.gesamtpreis_netto for p in self.positionen.all()), 2)

    @property
    def mwst_gesamt(self):
        return round(sum(p.mwst_betrag for p in self.positionen.all()), 2)

    @property
    def brutto(self):
        return round(self.netto + self.mwst_gesamt, 2)


    def gutschrift_status_aktualisieren(self):
        gutschriften = self.gutschriften.all()
        if not gutschriften.exists():
            # Keine Gutschriften mehr → zurück auf gesendet wenn nicht bezahlt
            if self.status in ('storniert', 'teilgutgeschrieben'):
                self.status = 'gesendet'
                self.save(update_fields=['status'])
            return
        gutschrift_summe = sum(g.brutto for g in gutschriften)
        if gutschrift_summe >= self.brutto:
            self.status = 'storniert'
        else:
            self.status = 'teilgutgeschrieben'
        self.save(update_fields=['status'])

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

class Gutschrift(models.Model):
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

    erstellt_am             = models.DateTimeField(auto_now_add=True)
    geaendert_am            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gutschrift'
        verbose_name_plural = 'Gutschriften'
        ordering = ['-datum', '-nummer']

    def __str__(self):
        return f'{self.nummer} – {self.kunde}'

    def save(self, *args, **kwargs):
        if not self.nummer:
            self.nummer = Einstellungen.laden().naechste_gutschriftnummer()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        rechnung = self.rechnung
        super().delete(*args, **kwargs)
        if rechnung:
            rechnung.gutschrift_status_aktualisieren()

    @property
    def netto(self):
        return round(sum(p.gesamtpreis_netto for p in self.positionen.all()), 2)

    @property
    def mwst_gesamt(self):
        return round(sum(p.mwst_betrag for p in self.positionen.all()), 2)

    @property
    def brutto(self):
        return round(self.netto + self.mwst_gesamt, 2)


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
