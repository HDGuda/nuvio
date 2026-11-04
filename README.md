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

* Firmenname sowie Vor- und Nachname des Ansprechpartners (getrennt erfasst)
* Adresse (Straße, PLZ, Ort, Land)
* Kontaktdaten (E-Mail, Telefon, Website)
* USt-IdNr.
* Freitextfeld für interne Notizen

Vor- und Nachname werden in Dokumenten und Listenansichten automatisch zu einem kombinierten Ansprechpartner zusammengeführt (z. B. „Schmidt, Max"), stehen in Einleitungs- und Schlusstexten aber auch einzeln als Platzhalter zur Verfügung (siehe [Platzhalter-System](#platzhalter-system)).

Die Kundenliste unterstützt eine Suchfunktion. Jeder Kunde kann bearbeitet oder gelöscht werden.

---

### Artikelstamm

Häufig verwendete Leistungen oder Produkte können im Artikelstamm hinterlegt und beim Erstellen von Dokumenten direkt eingefügt werden:

* Bezeichnung und Beschreibung
* Einheit (z. B. Std., Stk., pauschal)
* Einzelpreis
* Steuersatz (0 %, 7 %, 19 %)
* Aktiv/Inaktiv-Status

**Artikelübersicht:** Bundle-Artikel sind mit einem „Bundle"-Badge gekennzeichnet. Ihre Unter-Artikel (mit Menge, Einheit, Einzelpreis und Steuersatz) erscheinen leicht eingerückt direkt unter dem Bundle und sind standardmäßig eingeklappt. Ein Klick auf den Pfeil-Button vor dem Namen klappt sie auf bzw. zu. Zwischen den Haupt-Artikeln trennt eine kräftigere Linie. Die Bundle-Positionen werden per `prefetch_related` mitgeladen (keine N+1-Abfragen).

#### Bundle-Artikel

Artikel können als **Bundle** markiert werden. Ein Bundle-Artikel besteht aus mehreren Einzelartikeln, die im Artikelstamm gepflegt werden. Wird ein Bundle-Artikel in ein Angebot eingefügt, löst die App ihn automatisch in seine Einzelpositionen auf – jeder Einzelartikel erscheint als eigene Position im Angebot.

**Hinweise zur Verwendung:**

* Alle Einzelartikel eines Bundles müssen zuerst als eigenständige Artikel im Artikelstamm angelegt werden.
* Bundle-Artikel haben keinen eigenen Preis – der Gesamtpreis ergibt sich aus den Einzelartikeln. (Technisch speichert das Modell dennoch einen `einzelpreis` für das Bundle; die Artikelübersicht zeigt diesen Wert an.)
* Bundle-Artikel können nicht selbst Bestandteil eines anderen Bundles sein.
* Das Bundle-Feature steht aktuell für Angebote zur Verfügung.

**Ablauf:**

1. Einzelartikel anlegen (falls noch nicht vorhanden)
2. Neuen Artikel anlegen, Checkbox „Bundle-Artikel" aktivieren
3. Einzelartikel mit Menge und Reihenfolge zuweisen
4. Im Angebotsformular den Bundle-Artikel aus dem Artikelstamm wählen – die Einzelpositionen werden automatisch eingefügt

---

### Angebote

Angebote werden professionell erstellt, verwaltet und direkt aus der App versendet.

**Erstellung und Bearbeitung**

* Automatische Nummerierung nach konfigurierbarem Format (z. B. `AN-2026-0001`)
* Verknüpfung mit einem bestehenden Kunden
* Betreff (erscheint als Betreffzeile im PDF-Dokument, oberhalb des Einleitungstexts)
* Datum und Gültigkeitsdatum
* Frei bearbeitbarer Einleitungs- und Schlusstext (vorbelegt aus den Einstellungen) mit Platzhalter-Unterstützung
* Beliebig viele Positionen mit Bezeichnung, Beschreibung, Menge, Einheit, Einzelpreis (brutto, siehe [Preise, Steuer und Summenberechnung](#preise-steuer-und-summenberechnung)) und Steuersatz
* Einfügen von Bundle-Artikeln: automatische Auflösung in Einzelpositionen
* Reihenfolge der Positionen manuell festlegbar
* Interne Notizen (erscheinen nicht im PDF)

**Statusverwaltung**

Jedes Angebot durchläuft einen klar definierten Status:
`Entwurf` → `Gesendet` → `Angenommen` / `Abgelehnt` / `Abgelaufen`

**Ausgabe**

* PDF-Generierung (mit WeasyPrint) inkl. Betreffzeile und automatischer Seitennummerierung
* Optionale Hintergrundvorlage (z. B. eigenes Briefpapier als PDF)
* Direkter E-Mail-Versand aus der App heraus mit konfigurierbarer Betreffzeile und Textvorlage sowie bis zu zwei Standard-Anhängen

**Umwandlung in Rechnung**

Ein angenommenes Angebot kann mit einem Klick in eine Rechnung umgewandelt werden. Alle Positionen werden dabei übernommen, der Angebotsstatus wechselt automatisch auf „Angenommen". Die Rechnung erhält den Kleinunternehmer-Status, der zum Zeitpunkt der Umwandlung in den Einstellungen gilt (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg)).

---

### Rechnungen

Das Rechnungsmodul ist das Herzstück von nuvio.

**Erstellung und Bearbeitung**

* Automatische Nummerierung (z. B. `RE-2026-0001`)
* Verknüpfung mit Kunde und optionalem Ursprungsangebot
* Rechnungsdatum und Fälligkeitsdatum
* Einleitungs- und Schlusstext sowie Zahlungsbedingungen (aus Einstellungen vorbelegt) mit Platzhalter-Unterstützung
* Beliebig viele Positionen, analog zu Angeboten

**Leistungszeitraum**

Als vereinfachte Angabe des Leistungszeitpunkts (§ 14 UStG) ohne zusätzliches Datenbankfeld dient der Platzhalter `{{rechnung_leistungsmonat}}`. Er wird beim PDF-Export durch Monat und Jahr des Rechnungsdatums ersetzt. Im Standard-Einleitungstext für Rechnungen (Einstellungen → Standardtexte) steht dafür der Satz:

```
Die Leistungen wurden im {{rechnung_leistungsmonat}} erbracht.
```

Weicht der Leistungsmonat vom Rechnungsmonat ab, ersetzt man den Platzhalter im Einleitungstext der jeweiligen Rechnung durch festen Text (z. B. „im September 2026" oder „von August bis Oktober 2026"). Bereits gespeicherte Rechnungen enthalten den Satz nicht automatisch, weil der Standardtext nur beim Anlegen kopiert wird. Hinweis: Der Platzhalter folgt dem Rechnungsdatum – ändert man das Datum später, ändert sich auch der Monat im PDF.

**Statusverwaltung**

Rechnungen kennen folgende Zustände:
`Entwurf` → `Gesendet` → `Bezahlt` / `Teilbezahlt` / `Überfällig` / `Storniert` / `Teilgutgeschrieben`

**Zahlungserfassung**

* Teilzahlungen können einzeln mit Datum und Betrag erfasst werden
* Der offene Betrag wird automatisch aus Bruttobetrag abzüglich Gutschriften und Teilzahlungen berechnet
* Die Zahlungen stehen in der Detailansicht in der Karte „Zahlungseingang". Die früheren Modellfelder `bezahlt_am` und `bezahlt_betrag` an der Rechnung gibt es nicht mehr (Migration `0014`); die gleichnamigen Felder im Zahlungsformular dienen nur der Erfassung einer neuen Zahlung.

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
* Eine Gutschrift zu einer Rechnung übernimmt deren Kleinunternehmer-Status, damit beide Dokumente steuerlich gleich behandelt werden
* PDF-Generierung und E-Mail-Versand

---

### Preise, Steuer und Summenberechnung

**Preise werden brutto erfasst.** In den Positionen von Angeboten, Rechnungen und Gutschriften steht der Einzelpreis inkl. MwSt.; der Nettobetrag wird herausgerechnet. Im PDF und in den Detailansichten erscheinen die Einzelpreise netto (siehe aber [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg)).

**Summen je Steuersatz.** Die Summenberechnung ist für Angebote, Rechnungen und Gutschriften gleich (`SummenMixin` in `core/models.py`):

1. Die Positionen werden nach Steuersatz gruppiert (absteigend sortiert: 19 %, 7 %, 0 %).
2. Je Steuersatz wird die Brutto-Summe der Positionen gebildet.
3. Der Nettobetrag je Satz ergibt sich daraus **einmal** (nicht je Position), kaufmännisch auf Cent gerundet; die Steuer ist die Differenz aus Brutto und Netto.

Dadurch gilt immer **Netto + MwSt. = Brutto**, und der Bruttobetrag entspricht exakt der Summe der erfassten Positionsbeträge. Offener Betrag, Zahlungsabgleich und Gutschriftenverrechnung rechnen mit dem Bruttobetrag und sind davon unberührt; Cent-Abweichungen können sich nur bei Nettobetrag und MwSt. gegenüber der früheren Positionsrundung ergeben.

Die Eigenschaften der Dokumente:

| Eigenschaft | Inhalt |
|---|---|
| `steuergruppen` | Liste je Steuersatz mit `satz`, `brutto`, `netto`, `mwst` |
| `netto`, `mwst_gesamt`, `brutto` | Summen über alle Steuergruppen |

**Darstellung:** Pro Steuersatz eine Zeile „zzgl. 19 % MwSt. auf 600,00 €". Gibt es nur einen Steuersatz, steht die Zeile ohne „auf …". Das gilt für die drei PDF-Vorlagen und die drei Detailansichten.

```
Nettobetrag                          800,00 €
zzgl. 19 % MwSt. auf 600,00 €        114,00 €
zzgl.  7 % MwSt. auf 200,00 €         14,00 €
Gesamtbetrag                         928,00 €
```

---

### Kleinunternehmerregelung (§ 19 UStG)

nuvio unterstützt Kleinunternehmer, die keine Umsatzsteuer berechnen.

**Schalter:** Einstellungen → Steuer und Bank → Häkchen „Kleinunternehmer (§ 19 UStG)".

**Merkfeld pro Dokument:** Angebote, Rechnungen und Gutschriften haben ein Feld `kleinunternehmer` (nicht im Formular bearbeitbar). Es wird **beim Anlegen** des Dokuments aus den Einstellungen übernommen und ändert sich danach nicht mehr, auch nicht beim erneuten Speichern. Ein späteres Umlegen des Schalters wirkt daher nur auf neue Dokumente; bereits erstellte Dokumente behalten ihre Steuerbehandlung und ihr Aussehen.

* Eine Rechnung, die aus einem Angebot entsteht, erhält den Stand zum Zeitpunkt der Umwandlung.
* Eine Gutschrift zu einer Rechnung übernimmt den Status der Rechnung; eine freie Gutschrift den aktuellen Stand der Einstellungen.
* Nach der Migration gelten alle bereits vorhandenen Dokumente als „nicht Kleinunternehmer".

**Wirkung bei aktivem Kleinunternehmer-Status:**

* Berechnung: Alle Positionen zählen mit Steuersatz 0, es gilt Netto = Brutto und MwSt. = 0. Der erfasste Preis ist der Rechnungsbetrag.
* PDF: Die Spaltenköpfe lauten „Einzelpreis" und „Gesamtpreis" (ohne „netto"). Die Zeilen „Nettobetrag" und „zzgl. … % MwSt." entfallen, es bleibt nur der Gesamtbetrag (bei Gutschriften „Gutschriftbetrag"). Unter der Tabelle steht der Hinweis: „Der Auftragnehmer ist Kleinunternehmer im Sinne des § 19 UStG und stellt daher keine Umsatzsteuer in Rechnung."
* Detailansichten: In den Dokumentdaten steht „Steuer: Kleinunternehmer", die Summen-Karte zeigt nur den Gesamtbetrag samt Hinweis, in der Positionstabelle entfällt die MwSt.-Spalte.
* Formulare: Die Spalte heißt „Einzelpreis" (statt „Brutto-Einzelpreis"), die MwSt.-Spalte ist per CSS ausgeblendet (die Werte werden weiter mitgesendet, haben aber keine Wirkung), über der Tabelle steht ein Hinweis auf die Endpreise.

**Hinweise:**

* Die Steuernummer muss auf der Rechnung stehen. Sie erscheint in der Fußzeile, die die Vorlage ohne Briefpapier selbst rendert. Mit hinterlegtem Briefpapier muss sie in dessen Fußzeile eingedruckt sein (aktuell der Fall).
* Grenzen (seit 2025): 25.000 € Vorjahresumsatz und 100.000 € im laufenden Jahr. nuvio überwacht diese Grenzen nicht; der Schalter wird von Hand gesetzt. Die Anwendung der Regelung sollte mit dem Steuerberater abgestimmt sein.

---

### PDF-Layout (Angebote, Rechnungen, Gutschriften)

Die drei PDF-Vorlagen (`templates/angebote/pdf.html`, `rechnungen/pdf.html`, `gutschriften/pdf.html`) sind bewusst gleich aufgebaut:

* **Unterer Seitenrand:** Ist ein Hintergrund-PDF (Briefpapier) hinterlegt, beträgt der untere `@page`-Rand 28 mm, damit Inhalte nicht in die Fußzeile des Briefpapiers laufen. Ohne Briefpapier sind es 10 mm, die Fußzeile rendert die Vorlage dann selbst. Der Wert (`28mm`) ist an das Briefpapier angepasst und kann pro Vorlage geändert werden.
* **Summenblock:** Der Block mit Nettobetrag, MwSt.-Zeilen je Steuersatz und Gesamtbetrag (`tfoot` der Positionstabelle) ist als `display: table-row-group` mit `break-inside: avoid` gesetzt. Er erscheint nur einmal am Ende der Positionen und wird nicht auf jeder Seite wiederholt oder getrennt. Bei Kleinunternehmern besteht er nur aus dem Gesamtbetrag (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg)).
* **Kopfzeile:** Die Kopfzeile wiederholt sich auf jeder Seite; unter ihr sorgt `padding-bottom: 4mm` für Abstand, damit „Seite x von y" nicht auf der Tabellenkopfzeile sitzt.
* **Hinweis „Fortsetzung auf Seite n":** Bei mehrseitigen Dokumenten stempelt nuvio unten rechts ein kleines Etikett mit Pfeil auf jede Seite außer der letzten. Es wird nicht in den Vorlagen, sondern mit ReportLab in `seitennummern_einstempeln` (`views.py`) gezeichnet; Schrift 6,5 pt, Kästchenhöhe 12 pt, Abstand zur letzten Textzeile 5 mm.

---

### Platzhalter-System

In den Einleitungs- und Schlusstexten von Angeboten und Rechnungen – sowohl direkt im Dokument als auch in den vorbelegten Standardtexten unter Einstellungen – können Platzhalter eingefügt werden, die beim PDF-Export automatisch durch echte Werte ersetzt werden. Über das Dropdown „Platzhalter einfügen…" im Editor lassen sich folgende Variablen einfügen (Ausnahme: `{{rechnung_leistungsmonat}}`, siehe unten):

| Platzhalter | Ersetzt durch |
|---|---|
| `{{kunde_firma}}` | Firmenname des Kunden |
| `{{kunde_ansprechpartner}}` | Vor- und Nachname kombiniert (z. B. „Schmidt, Max") |
| `{{kunde_vorname}}` | Nur Vorname des Kunden |
| `{{kunde_nachname}}` | Nur Nachname des Kunden |
| `{{kunde_ort}}` | Ort des Kunden |
| `{{angebot_nummer}}` | Angebotsnummer (nur in Angeboten) |
| `{{angebot_datum}}` | Angebotsdatum (nur in Angeboten) |
| `{{rechnung_nummer}}` | Rechnungsnummer (nur in Rechnungen) |
| `{{rechnung_datum}}` | Rechnungsdatum (nur in Rechnungen) |
| `{{rechnung_leistungsmonat}}` | Monat und Jahr des Rechnungsdatums, z. B. „Oktober 2026" (nur in Rechnungen) |
| `---seitenumbruch---` | Erzwungener Seitenumbruch im PDF |

> **Hinweis:** `{{rechnung_leistungsmonat}}` ist noch nicht im Dropdown „Platzhalter einfügen…" enthalten und muss vorerst von Hand eingetippt werden (siehe To do).

Die **E-Mail-Vorlagen** (Betreff und Text für Angebote, Rechnungen und Gutschriften) verwenden ein eigenes, kleineres Platzhalter-Set, das unabhängig vom oben genannten System funktioniert:

| Platzhalter | Ersetzt durch |
|---|---|
| `{{nummer}}` | Dokumentnummer |
| `{{kundenname}}` | Firmenname, sonst kombinierter Ansprechpartner |
| `{{firma}}` | Eigener Firmenname (aus den Einstellungen) |
| `{{datum}}` | Dokumentdatum |

> **Bekannte Einschränkung:** In den E-Mail-Vorlagen stehen `{{kunde_vorname}}` und `{{kunde_nachname}}` aktuell *nicht* getrennt zur Verfügung – nur das kombinierte `{{kundenname}}`. Eine Erweiterung ist möglich, aber noch nicht umgesetzt.

---

### Einstellungen

Alle zentralen Parameter der Anwendung werden einmalig in den Einstellungen hinterlegt:

**Firmendaten**

* Firmenname, Zusatzzeilen (z. B. Berufsbezeichnung, Registernummer), Adresse, Telefon, E-Mail, Website
* Logo (wird in Dokumenten eingebunden)
* Hintergrund-PDF (eigenes Briefpapier für alle Dokumente)

**Steuer und Bank**

* Steuernummer, USt-IdNr., Bankverbindung (IBAN, BIC)
* Schalter „Kleinunternehmer (§ 19 UStG)" (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg))

**Nummernkreise**

* Konfigurierbares Format für Angebots-, Rechnungs- und Gutschriftnummern
* Frei wählbarer Präfix und fortlaufende Nummerierung (mit Jahr)
* Nächste Nummer manuell einstellbar

**Standardtexte**

* Vorbelegte Einleitungs- und Schlusstexte für Angebote und Rechnungen, inklusive Platzhalter-Dropdown (siehe [Platzhalter-System](#platzhalter-system))
* Standard-Zahlungsbedingungen

**E-Mail-Vorlagen**

* Separate Betreff- und Textvorlagen für Angebote, Rechnungen und Gutschriften
* Platzhalter für Nummer, Kundenname, Firma und Datum (siehe [Platzhalter-System](#platzhalter-system))
* Bis zu zwei Standard-Anhänge je Dokumenttyp

---

## Technischer Stack

* **Backend:** Python / Django
* **Datenbank:** SQLite (lokal, keine externe Datenbank nötig)
* **PDF-Generierung:** WeasyPrint + pypdf (Hintergrundmerge, Seitennummern mit ReportLab)
* **Frontend:** HTML/CSS (eigene Templates, ohne JavaScript-Framework; kleine Inline-Skripte, z. B. für das Auf-/Zuklappen der Bundle-Unterartikel und für die Positionszeilen in den Formularen)
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

### Nach Änderungen am Datenmodell

Nach Änderungen an `models.py` immer `makemigrations` und `migrate` ausführen und vorher eine Datensicherung anlegen. Mit `makemigrations --check` lässt sich prüfen, ob Modelle und Migrationen übereinstimmen („No changes detected").

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
│   ├── models.py            # Datenmodell (Kunden, Artikel, Bundles, Angebote, Rechnungen, Gutschriften, SummenMixin)
│   ├── views.py             # Alle Ansichten und PDF-/E-Mail-Logik
│   ├── forms.py             # Django-Formulare und Formsets
│   ├── middleware.py        # Login-Schutz für alle Seiten
│   ├── templatetags/
│   │   └── nuvio_filters.py # Eigene Template-Filter (Datum, Euro, Platzhalter-Ersetzung)
│   └── migrations/          # Datenbankmigrationen
├── rechnungssystem/         # Django-Projektkonfiguration
│   ├── settings.py          # Entwicklungseinstellungen
│   ├── settings_prod.py     # Produktionseinstellungen
│   └── urls.py              # URL-Konfiguration inkl. Login/Logout
├── templates/               # HTML-Templates (Dashboard, Listen, Formulare, PDFs, E-Mails)
│   └── login.html           # Anmeldeseite im Nuvio-Design
├── manage.py                # Django-Management-Utility
└── start.bat                # Schnellstart für Windows
```

---

## Letzte Änderungen (3. November 2026)

* **Summenblock nach Steuersätzen:** Eine MwSt.-Zeile je Steuersatz mit Bemessungsgrundlage in den drei PDF-Vorlagen und den drei Detailansichten (vorher wurde nur der Satz der ersten Position ausgewiesen). Die Berechnung läuft gemeinsam über `SummenMixin` aus der Brutto-Summe je Satz; `Netto + MwSt. = Brutto` gilt jetzt auch bei Gutschriften immer.
* **Kleinunternehmerregelung:** Neuer Schalter in den Einstellungen, Merkfeld `kleinunternehmer` pro Angebot, Rechnung und Gutschrift (beim Anlegen festgehalten), Gutschrift übernimmt den Status der Rechnung. PDF-Vorlagen, Detailansichten und Formulare passen sich an (nur Gesamtbetrag, Hinweis auf § 19 UStG, MwSt.-Spalte im Formular ausgeblendet).
* **Migration `0014`:** Enthält die vier neuen Felder `kleinunternehmer` sowie nachgeholte Modelländerungen (entfernte Felder `bezahlt_am`, `bezahlt_betrag` und `vorlage` an der Rechnung, kleinere Feldanpassungen).
* **Rechnungs-Detailansicht:** Status-Badge zeigt den Status wieder im Badge, die Abfrage des nicht mehr vorhandenen Felds `bezahlt_am` ist entfernt.
* **PDF-Hinweis „Fortsetzung auf Seite n":** Dezenter gestaltet (kleinere Schrift, kleineres Kästchen und kleinerer Pfeil).

### Davor (2. November 2026)

* **Artikelübersicht:** Bundle-Unterartikel eingerückt und standardmäßig eingeklappt (Pfeil-Button), „Bundle"-Badge, kräftigere Trennlinie zwischen Haupt-Artikeln, `prefetch_related` in `artikel_liste`.
* **PDF-Seitenumbruch:** Unterer Seitenrand bei Briefpapier 28 mm, damit der Summenblock nicht mehr in die Fußzeile läuft (Angebote, Rechnungen, Gutschriften).
* **PDF-Summenblock:** Nettobetrag/MwSt./Gesamtbetrag erscheinen nur einmal am Ende der Positionstabelle (`display: table-row-group`) statt auf jeder Seite.
* **PDF-Kopfzeile:** Zusätzlicher Abstand unter der Kopfzeile, damit die Seitennummer nicht auf der Tabellenkopfzeile sitzt.
* **Leistungszeitraum:** Neuer Platzhalter `{{rechnung_leistungsmonat}}` (ohne neues Datenbankfeld) für die vereinfachte Angabe des Leistungsmonats auf Rechnungen.

---

## To do

Reihenfolge nach Priorität. Reverse Charge ist für uns nicht relevant und wird nicht umgesetzt.

### 1. Unveränderbarkeit (GoBD)

* Versendete oder bezahlte Rechnungen dürfen nicht mehr bearbeitet oder gelöscht werden, nur noch storniert bzw. per Gutschrift korrigiert.
* Sperrlogik in Views und Formularen, Hinweis in der Oberfläche; Konzept mit dem Steuerberater abstimmen.
* **Noch zu klären:** Ab welchem Status wird gesperrt (ab „Gesendet" oder erst ab „Bezahlt")? Wie werden Fehler korrigiert (nur Gutschrift plus neue Rechnung, oder zusätzlich ein Storno-Vorgang)? Sollen auch versendete Gutschriften gesperrt werden?
* Vorarbeit ist geleistet: Der Steuerstatus ist bereits pro Dokument festgehalten (Merkfeld `kleinunternehmer`).

### 2. Bessere Wartbarkeit (doppelter Code)

* Gemeinsames Basis-Template für die drei PDF-Vorlagen (`{% extends %}` mit Blöcken für Titel, Meta-Tabelle, Empfänger, Schlusstext), damit Layoutänderungen nur einmal nötig sind. Die Steuerzeilen- und Kleinunternehmer-Logik steckt inzwischen in je drei PDF-, Detail- und Formularvorlagen (gemeinsame Includes würden das vereinfachen).
* Hilfsfunktion in `views.py` für die PDF-Erzeugung (WeasyPrint, Seitennummern, Hintergrund), die bisher für Angebot, Rechnung und Gutschrift (Ansicht und E-Mail) mehrfach vorkommt.
* Automatische Tests für Summenberechnung (gemischte Steuersätze, Kleinunternehmer, Cent-Rundung), offenen Betrag, Gutschriften-Verrechnung, Nummernkreise und das Merkfeld `kleinunternehmer`.

### 3. Dokument duplizieren

* Funktion „Kopie erstellen" für Angebote und Rechnungen (Positionen, Texte und Kunde übernehmen; neue Nummer, Status `Entwurf`, aktuelles Datum). Der Kleinunternehmer-Status der Kopie folgt dabei dem aktuellen Stand der Einstellungen.

### Weitere offene Punkte

* Steuerhinweis bei 0 %-Positionen (Freitext, z. B. Befreiungsgrund): bisher nur über den Schlusstext möglich, ggf. später eigenes Feld.
* Kleinunternehmer-Hinweistext ist fest in den PDF-Vorlagen hinterlegt; ggf. in den Einstellungen editierbar machen.
* Gutschrift von Hand anlegen und im Formular eine Rechnung wählen: Das Formular zeigt den Hinweis zunächst nach dem aktuellen Stand der Einstellungen, gespeichert wird der Status der Rechnung.
* Rechnungs-Detailansicht: Datum der letzten Zahlung in den Rechnungsdaten anzeigen (optional, als Eigenschaft aus den Zahlungen).
* Platzhalter `{{rechnung_leistungsmonat}}` im Dropdown „Platzhalter einfügen…" ergänzen (Rechnungsformular und Einstellungen).
* Bundle-Artikel auch in Rechnungen und Gutschriften einfügbar machen (aktuell nur in Angeboten).
* `{{kunde_vorname}}` und `{{kunde_nachname}}` in den E-Mail-Vorlagen ergänzen.
