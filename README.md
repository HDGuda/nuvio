# nuvio – Office-Software für Freiberufler

nuvio ist eine schlanke, lokal betriebene Office-Webanwendung für Freiberufler und Selbstständige. Sie läuft als Django-Anwendung auf dem eigenen Rechner und wird bequem über den Browser bedient – ohne Cloud-Abhängigkeit, ohne Abonnement.

---

## Funktionsübersicht

### Dashboard

Beim Start zeigt nuvio ein übersichtliches Dashboard mit den wichtigsten Kennzahlen auf einen Blick:

* Anzahl offener Angebote
* Anzahl offener Rechnungen
* Anzahl bezahlter Rechnungen
* Listenvorschau der zuletzt erstellten Angebote und Rechnungen

Von hier aus kann direkt ein neues Angebot oder eine neue Rechnung erstellt werden.

---

### Kundenverwaltung

Kunden werden mit vollständigen Stammdaten gepflegt:

* Firmenname und Ansprechpartner
* Adresse (Straße, PLZ, Ort, Land)
* Kontaktdaten (E-Mail, Telefon, Website)
* USt-IdNr.
* Freitextfeld für interne Notizen

Die Kundenliste unterstützt eine Suchfunktion. Jeder Kunde kann bearbeitet oder gelöscht werden.

---

### Artikelstamm

Häufig verwendete Leistungen oder Produkte können im Artikelstamm hinterlegt und beim Erstellen von Dokumenten direkt eingefügt werden:

* Bezeichnung und Beschreibung
* Einheit (z. B. Std., Stk., pauschal)
* Einzelpreis
* Steuersatz (0 %, 7 %, 19 %)
* Aktiv/Inaktiv-Status

---

### Angebote

Angebote werden professionell erstellt, verwaltet und direkt aus der App versendet.

**Erstellung und Bearbeitung**

* Automatische Nummerierung nach konfigurierbarem Format (z. B. `AN-2026-0001`)
* Verknüpfung mit einem bestehenden Kunden
* Datum und Gültigkeitsdatum
* Frei bearbeitbarer Einleitungs- und Schlusstext (vorbelegt aus den Einstellungen)
* Beliebig viele Positionen mit Bezeichnung, Beschreibung, Menge, Einheit, Einzelpreis und Steuersatz
* Reihenfolge der Positionen manuell festlegbar
* Interne Notizen (erscheinen nicht im PDF)

**Statusverwaltung**

Jedes Angebot durchläuft einen klar definierten Status:
`Entwurf` → `Gesendet` → `Angenommen` / `Abgelehnt` / `Abgelaufen`

**Ausgabe**

* PDF-Generierung (mit WeasyPrint) inkl. automatischer Seitennummerierung
* Optionale Hintergrundvorlage (z. B. eigenes Briefpapier als PDF)
* Direkter E-Mail-Versand aus der App heraus mit konfigurierbarer Betreffzeile und Textvorlage sowie bis zu zwei Standard-Anhängen

**Umwandlung in Rechnung**

Ein angenommenes Angebot kann mit einem Klick in eine Rechnung umgewandelt werden. Alle Positionen werden dabei übernommen, der Angebotsstatus wechselt automatisch auf „Angenommen".

---

### Rechnungen

Das Rechnungsmodul ist das Herzstück von nuvio.

**Erstellung und Bearbeitung**

* Automatische Nummerierung (z. B. `RE-2026-0001`)
* Verknüpfung mit Kunde und optionalem Ursprungsangebot
* Rechnungsdatum und Fälligkeitsdatum
* Einleitungs- und Schlusstext sowie Zahlungsbedingungen (aus Einstellungen vorbelegt)
* Beliebig viele Positionen, analog zu Angeboten

**Statusverwaltung**

Rechnungen kennen folgende Zustände:
`Entwurf` → `Gesendet` → `Bezahlt` / `Teilbezahlt` / `Überfällig` / `Storniert` / `Teilgutgeschrieben`

**Zahlungserfassung**

* Teilzahlungen können einzeln mit Datum und Betrag erfasst werden
* Der offene Betrag wird automatisch aus Bruttobetrag abzüglich Gutschriften und Teilzahlungen berechnet

**Ausgabe**

* PDF-Generierung inkl. Seitennummerierung und optionalem Briefpapier-Hintergrund
* E-Mail-Versand mit vorausgefülltem Betreff und Text sowie Standard-Anhängen

---

### Gutschriften

Gutschriften können eigenständig oder als Korrekturdokument zu einer bestehenden Rechnung erstellt werden.

* Automatische Nummerierung (z. B. `GS-2026-0001`)
* Optionale Verknüpfung mit einer Rechnung
* Eigene Positionen mit Mengen, Preisen und Steuersätzen
* Statusverwaltung: `Entwurf` → `Gesendet` → `Storniert`
* Wird eine Gutschrift mit einer Rechnung verknüpft, aktualisiert sich deren Status automatisch (z. B. auf „Teilgutgeschrieben" oder „Storniert")
* PDF-Generierung und E-Mail-Versand

---

### Einstellungen

Alle zentralen Parameter der Anwendung werden einmalig in den Einstellungen hinterlegt:

**Firmendaten**

* Firmenname, Zusatzzeilen, Adresse, Telefon, E-Mail, Website
* Logo (wird in Dokumenten eingebunden)
* Hintergrund-PDF (eigenes Briefpapier für alle Dokumente)

**Steuer und Bank**

* Steuernummer, USt-IdNr., Bankverbindung (IBAN, BIC)

**Nummernkreise**

* Konfigurierbares Format für Angebots-, Rechnungs- und Gutschriftnummern
* Frei wählbarer Präfix und fortlaufende Nummerierung (mit Jahr)
* Nächste Nummer manuell einstellbar

**Standardtexte**

* Vorbelegte Einleitungs- und Schlusstexte für Angebote und Rechnungen
* Standard-Zahlungsbedingungen

**E-Mail-Vorlagen**

* Separate Betreff- und Textvorlagen für Angebote, Rechnungen und Gutschriften
* Platzhalter für Nummer, Kundenname, Firma und Datum
* Bis zu zwei Standard-Anhänge je Dokumenttyp

---

## Technischer Stack

* **Backend:** Python / Django
* **Datenbank:** SQLite (lokal, keine externe Datenbank nötig)
* **PDF-Generierung:** WeasyPrint + pypdf (Hintergrundmerge, Seitennummern mit ReportLab)
* **Frontend:** HTML/CSS (eigene Templates, ohne JavaScript-Framework)
* **Betrieb:** Lokaler Django-Entwicklungsserver, Start per `start.bat` (Windows)

---

## Installation und Start

### Voraussetzungen

* Python 3.x
* Virtuelle Umgebung mit installierten Abhängigkeiten (`pip install -r requirements.txt`)
* WeasyPrint (für PDF-Erzeugung, optional, aber empfohlen)

### Start unter Windows

```
start.bat
```

Die Datei startet den Django-Server und öffnet automatisch `http://127.0.0.1:8000` im Browser.

**Entwicklungsmodus (Standard):**

```
venv\Scripts\python.exe manage.py runserver
```

**Produktionsmodus:**

```
venv\Scripts\python.exe manage.py runserver --settings=rechnungssystem.settings_prod
```

### Erster Start

Beim ersten Start müssen die Datenbankmigrationen angewendet, ein Benutzer angelegt und die Einstellungen befüllt werden:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Anschließend unter `http://127.0.0.1:8000` mit den gewählten Zugangsdaten anmelden und die Einstellungen aufrufen, um Firmendaten, Nummernkreise und E-Mail-Vorlagen einzurichten.

---

## Authentifizierung

nuvio ist durch eine einfache Benutzeranmeldung geschützt. Alle Seiten der Anwendung sind nur nach erfolgreicher Anmeldung erreichbar.

* Der Login erfolgt über `/login/`
* Die Abmeldung ist jederzeit über den „Abmelden"-Link in der Seitenleiste möglich
* Benutzerverwaltung (weitere Nutzer anlegen, Passwörter ändern) über das Django-Admininterface unter `/admin/`

---

## Projektstruktur

```
nuvio/
├── core/                    # Hauptmodul: Models, Views, Forms, URLs
│   ├── models.py            # Datenmodell (Kunden, Artikel, Angebote, Rechnungen, Gutschriften)
│   ├── views.py             # Alle Ansichten und PDF-/E-Mail-Logik
│   ├── forms.py             # Django-Formulare und Formsets
│   └── middleware.py        # Login-Schutz für alle Seiten
├── rechnungssystem/         # Django-Projektkonfiguration
│   ├── settings.py          # Entwicklungseinstellungen
│   ├── settings_prod.py     # Produktionseinstellungen
│   └── urls.py              # URL-Konfiguration inkl. Login/Logout
├── templates/               # HTML-Templates (Dashboard, Listen, Formulare, PDFs, E-Mails)
│   └── login.html           # Anmeldeseite im Nuvio-Design
├── manage.py                # Django-Management-Utility
└── start.bat                # Schnellstart für Windows
```
