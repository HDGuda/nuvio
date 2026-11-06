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

Vor- und Nachname werden in Dokumenten und PDFs zu „Vorname Nachname“ zusammengeführt (z. B. „Max Schmidt“), in Listenansichten als „Nachname, Vorname“ angezeigt (z. B. „Schmidt, Max“). In Einleitungs- und Schlusstexten stehen sie auch einzeln als Platzhalter zur Verfügung (siehe [Platzhalter-System](#platzhalter-system)).

Die Kundenliste unterstützt eine Suchfunktion. Jeder Kunde kann bearbeitet oder gelöscht werden.

---

### Artikelstamm

Häufig verwendete Leistungen oder Produkte können im Artikelstamm hinterlegt und beim Erstellen von Dokumenten direkt eingefügt werden:

* Bezeichnung und Beschreibung
* Einheit (z. B. Std., Stk., pauschal)
* Einzelpreis
* Steuersatz (0 %, 7 %, 19 %)
* Aktiv/Inaktiv-Status

**Artikelübersicht:** Bundle-Artikel sind mit einem „Bundle“-Badge gekennzeichnet. Ihre Unter-Artikel (mit Menge, Einheit, Einzelpreis und Steuersatz) erscheinen leicht eingerückt direkt unter dem Bundle und sind standardmäßig eingeklappt. Ein Klick auf den Pfeil-Button vor dem Namen klappt sie auf bzw. zu. Zwischen den Haupt-Artikeln trennt eine kräftigere Linie. Die Bundle-Positionen werden per `prefetch_related` mitgeladen (keine N+1-Abfragen).

#### Bundle-Artikel

Artikel können als **Bundle** markiert werden. Ein Bundle-Artikel besteht aus mehreren Einzelartikeln, die im Artikelstamm gepflegt werden. Wird ein Bundle-Artikel in ein Angebot eingefügt, löst die App ihn automatisch in seine Einzelpositionen auf – jeder Einzelartikel erscheint als eigene Position im Angebot.

**Hinweise zur Verwendung:**

* Alle Einzelartikel eines Bundles müssen zuerst als eigenständige Artikel im Artikelstamm angelegt werden.
* Bundle-Artikel haben keinen eigenen Preis – der Gesamtpreis ergibt sich aus den Einzelartikeln. (Technisch speichert das Modell dennoch einen `einzelpreis` für das Bundle; die Artikelübersicht zeigt diesen Wert an, siehe To do.)
* Bundle-Artikel können nicht selbst Bestandteil eines anderen Bundles sein.
* Das Bundle-Feature steht aktuell für Angebote zur Verfügung.

**Ablauf:**

1. Einzelartikel anlegen (falls noch nicht vorhanden)
2. Neuen Artikel anlegen, Checkbox „Bundle-Artikel“ aktivieren
3. Einzelartikel mit Menge und Reihenfolge zuweisen
4. Im Angebotsformular den Bundle-Artikel aus dem Artikelstamm wählen – die Einzelpositionen werden automatisch eingefügt

---

### Absenderprofile (Rollen)

Der Aussteller aller Dokumente ist immer derselbe Unternehmer, tritt aber in unterschiedlichen Rollen auf (z. B. als Energieberater, Unternehmensberater oder freiberuflicher Redakteur). Ein **Absenderprofil** legt fest, wie ein Dokument aussieht. Es ist ausdrücklich **kein Mandant**: Alle Profile teilen sich denselben Nummernkreis, dieselben Steuer- und Bankdaten, dieselben Standardtexte und E-Mail-Vorlagen sowie den Kleinunternehmer-Schalter aus den Einstellungen.

**Inhalt eines Profils**

| Feld | Bedeutung |
|---|---|
| Bezeichnung (intern) | Name des Profils, nur in nuvio sichtbar |
| Standardprofil | Genau ein Profil ist bei neuen Dokumenten vorausgewählt |
| Firmenname im Dokument | Fett im Briefkopf; ersetzt `{{firma}}` in E-Mails. Leer = „Name“ aus den Stammdaten |
| Logo und Logo-Position | Links oder rechts oben im Briefkopf |
| Briefkopf links | Mehrzeiliger Text unter dem Firmennamen (Zusatzzeilen, Straße, Ort, E-Mail) |
| Briefkopf rechts | Mehrzeiliger Text oben rechts; wird nur angezeigt, wenn das Logo links steht (maximal etwa 4 Zeilen) |
| Absenderzeile | Kleine Zeile über der Empfängeradresse im Adressfenster, z. B. „Name · Straße · PLZ Ort“ |
| Hintergrund-PDF | Briefpapier; eine Seite genügt, sie wird für alle Seiten des Dokuments verwendet |
| Unterer Seitenrand (mm) | Muss zur Fußzeile des Briefpapiers passen (Standard 28 mm) |
| Thunderbird-Identität | Nummer der Absender-Identität in Thunderbird (z. B. `id2`); bestimmt die Absenderadresse der E-Mail. Leer = Standard-Identität von Thunderbird |

**Verwaltung:** Einstellungen → Karte „Absenderprofile“ → „Absenderprofile verwalten“ (Liste mit Logo, Briefpapier und Zahl der Dokumente, Bearbeiten, „Als Standard“, Löschen). Zusätzlich ist das Modell im Django-Admin registriert. Ein Profil, das Rechnungen, Angebote oder Gutschriften verwenden, und das Standardprofil lassen sich nicht löschen. Beim Ersetzen von Logo oder Briefpapier ist nur ein Austausch möglich, kein ersatzloses Entfernen.

**Zuordnung zu Dokumenten**

* **Rechnung und Angebot:** Dropdown „Absenderprofil“ im Formular, vorbelegt mit dem Standardprofil. Das Profil steht auch in der Detailansicht („Absender“).
* **Angebot → Rechnung:** Die Rechnung übernimmt das Profil des Angebots.
* **Gutschrift:** Eine Gutschrift, die aus einer Rechnung erzeugt wird, übernimmt deren Profil. Im Formular ist das Profil ebenfalls wählbar (vorbelegt mit dem Standardprofil), damit auch eine freie Gutschrift ein anderes Profil bekommen kann.
* Dokumente ohne Zuordnung nutzen automatisch das Standardprofil.

**Erstes Profil:** Existiert noch kein Profil, legt nuvio das Profil „Standard“ beim ersten Bedarf aus den Stammdaten an (`Absenderprofil.standard()`). Beim Update auf die Version mit Absenderprofilen übernimmt die Migration `0015` Logo, Briefpapier und Adresse aus den bisherigen Einstellungen und weist allen vorhandenen Rechnungen dieses Profil zu (`0016` für Angebote, `0017` für Gutschriften, `0018` für die Thunderbird-Identität).

---

### Angebote

Angebote werden professionell erstellt, verwaltet und direkt aus der App versendet.

**Erstellung und Bearbeitung**

* Automatische Nummerierung nach konfigurierbarem Format (z. B. `AN-2026-0001`)
* Verknüpfung mit einem bestehenden Kunden
* Absenderprofil (siehe [Absenderprofile](#absenderprofile-rollen))
* Betreff (erscheint als fette Betreffzeile im PDF-Dokument, oberhalb des Einleitungstexts)
* Datum und Gültigkeitsdatum
* Frei bearbeitbarer Einleitungs- und Schlusstext mit Platzhalter-Unterstützung; die Standardtexte aus den Einstellungen sind schon beim Anlegen im Formular vorbelegt
* Beliebig viele Positionen mit Bezeichnung, Beschreibung, Menge, Einheit, Einzelpreis (brutto, siehe [Preise, Steuer und Summenberechnung](#preise-steuer-und-summenberechnung)) und Steuersatz
* Einfügen von Bundle-Artikeln: automatische Auflösung in Einzelpositionen
* Reihenfolge der Positionen manuell festlegbar
* Interne Notizen (erscheinen nicht im PDF)

**Statusverwaltung**

Jedes Angebot durchläuft einen klar definierten Status:
`Entwurf` → `Gesendet` → `Angenommen` / `Abgelehnt` / `Abgelaufen`

**Ausgabe**

* PDF-Generierung (mit WeasyPrint) mit Briefkopf, Logo und Briefpapier aus dem Absenderprofil, Adressfenster für Fensterumschläge und automatischer Seitennummerierung (siehe [PDF-Layout](#pdf-layout-angebote-rechnungen-gutschriften))
* E-Mail-Versand aus der App heraus: nuvio öffnet in Thunderbird ein Schreibfenster (Empfänger, Betreff, Text und PDF als Anhang, Absenderadresse laut Absenderprofil) mit konfigurierbarer Betreffzeile und Textvorlage sowie bis zu zwei Standard-Anhängen; gesendet wird erst per Klick in Thunderbird (siehe [E-Mail-Übergabe an Thunderbird](#e-mail-übergabe-an-thunderbird))

**Umwandlung in Rechnung**

Ein angenommenes Angebot kann mit einem Klick in eine Rechnung umgewandelt werden. Alle Positionen werden dabei übernommen, der Angebotsstatus wechselt automatisch auf „Angenommen“. Die Rechnung erhält den Kleinunternehmer-Status, der zum Zeitpunkt der Umwandlung in den Einstellungen gilt (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg)), und das Absenderprofil des Angebots.

---

### Rechnungen

Das Rechnungsmodul ist das Herzstück von nuvio.

**Erstellung und Bearbeitung**

* Automatische Nummerierung (z. B. `RE-2026-0001`), gemeinsam für alle Absenderprofile
* Verknüpfung mit Kunde und optionalem Ursprungsangebot
* Absenderprofil (siehe [Absenderprofile](#absenderprofile-rollen))
* Rechnungsdatum und Fälligkeitsdatum
* Einleitungs- und Schlusstext sowie Zahlungsbedingungen mit Platzhalter-Unterstützung; die Standardtexte aus den Einstellungen sind schon beim Anlegen im Formular vorbelegt (bleibt ein Feld leer, setzt nuvio beim Speichern weiterhin den Standardtext ein)
* Beliebig viele Positionen, analog zu Angeboten

**Leistungszeitraum**

Als vereinfachte Angabe des Leistungszeitpunkts (§ 14 UStG) ohne zusätzliches Datenbankfeld dient der Platzhalter `{{rechnung_leistungsmonat}}`. Er wird beim PDF-Export durch Monat und Jahr des Rechnungsdatums ersetzt. Im Standard-Einleitungstext für Rechnungen (Einstellungen → Standardtexte) steht dafür der Satz:

```
Die Leistungen wurden im {{rechnung_leistungsmonat}} erbracht.
```

Weicht der Leistungsmonat vom Rechnungsmonat ab, ersetzt man den Platzhalter im Einleitungstext der jeweiligen Rechnung durch festen Text (z. B. „im September 2026“ oder „von August bis Oktober 2026“). Bereits gespeicherte Rechnungen enthalten den Satz nicht automatisch, weil der Standardtext nur beim Anlegen kopiert wird. Hinweis: Der Platzhalter folgt dem Rechnungsdatum – ändert man das Datum später, ändert sich auch der Monat im PDF (bei gesperrten Rechnungen nicht mehr, siehe unten).

**Statusverwaltung**

Rechnungen kennen folgende Zustände:
`Entwurf` → `Gesendet` → `Bezahlt` / `Teilbezahlt` / `Überfällig` / `Storniert` / `Teilgutgeschrieben`

**Zahlungserfassung**

* Teilzahlungen können einzeln mit Datum und Betrag erfasst werden
* Der offene Betrag wird automatisch aus Bruttobetrag abzüglich Gutschriften und Teilzahlungen berechnet. Ist er nach einer Zahlung 0 oder kleiner, wechselt der Status auf „Bezahlt“, sonst auf „Teilbezahlt“ (Gutschriften werden dabei berücksichtigt)
* Die Zahlungen stehen in der Detailansicht in der Karte „Zahlungseingang“. Die früheren Modellfelder `bezahlt_am` und `bezahlt_betrag` an der Rechnung gibt es nicht mehr (Migration `0014`); die gleichnamigen Felder im Zahlungsformular dienen nur der Erfassung einer neuen Zahlung.

**Unveränderbarkeit (GoBD)**

Eine Rechnung ist **ab dem Status „Bezahlt“ dauerhaft gesperrt**:

* Maßgeblich ist nicht der Status, sondern das Feld `gesperrt_am`. Es wird einmalig gesetzt, sobald eine Rechnung bezahlt ist (durch eine Zahlung, die den offenen Betrag auf 0 bringt, oder durch manuelles Setzen des Status „Bezahlt“ im Formular; das Status-Dropdown warnt davor), und nie zurückgenommen. Eine Gutschrift kann den Status später auf „Teilgutgeschrieben“ oder „Storniert“ ändern, die Sperre bleibt. Wird eine Gutschrift wieder gelöscht, fällt eine gesperrte Rechnung auf „Bezahlt“ zurück. Bei der Migration `0015` wurden bereits bezahlte Rechnungen gesperrt.
* Gesperrt sind Kunde, Datum, Absenderprofil, Positionen, Texte, Beträge, Kleinunternehmer-Merkfeld und Löschen. In der Detailansicht fehlt der Button „Bearbeiten“ und eine Zeile „Gesperrt“ nennt das Datum; der Bearbeiten-Link leitet mit Hinweis zurück. Die Sperre gilt auch auf Modellebene (`Rechnung.save()`, `delete()`, `RechnungPosition`), also zusätzlich zu den Formularen, etwa für den Django-Admin. Es wird dort `RechnungGesperrt` ausgelöst.
* Weiterhin möglich sind Zahlungen erfassen, Statuswechsel durch Gutschriften sowie (auf Modellebene) Status, Versanddatum und interne Notizen. Korrekturen laufen über Gutschrift und neue Rechnung.
* **PDF-Archiv:** Beim Sperren speichert nuvio das PDF einmalig als Datei (`media/rechnungen_archiv/`, Feld `pdf_archiv`) und liefert danach nur noch dieses Archiv aus, auch beim E-Mail-Versand. Spätere Änderungen an Kundendaten oder am Profil verändern eine bezahlte Rechnung damit nicht mehr. Bei bereits vorhandenen bezahlten Rechnungen entsteht das Archiv beim ersten Abruf des PDFs.
* Bis zur Zahlung (Status Entwurf, Gesendet usw.) ist eine Rechnung änderbar; das PDF wird dann bei jedem Aufruf frisch erzeugt.

**Ausgabe**

* PDF-Generierung inkl. Seitennummerierung und Briefpapier aus dem Absenderprofil
* E-Mail-Versand mit vorausgefülltem Betreff und Text sowie Standard-Anhängen, über die Thunderbird-Identität des Profils

---

### Gutschriften

Gutschriften können eigenständig oder als Korrekturdokument zu einer bestehenden Rechnung erstellt werden.

* Automatische Nummerierung (z. B. `GS-2026-0001`)
* Optionale Verknüpfung mit einer Rechnung
* Eigene Positionen mit Mengen, Preisen und Steuersätzen
* Statusverwaltung: `Entwurf` → `Gesendet` → `Storniert`
* Wird eine Gutschrift mit einer Rechnung verknüpft, aktualisiert sich deren Status automatisch (z. B. auf „Teilgutgeschrieben“ oder „Storniert“); das ist auch bei gesperrten Rechnungen möglich
* Eine Gutschrift zu einer Rechnung übernimmt deren Kleinunternehmer-Status, damit beide Dokumente steuerlich gleich behandelt werden, und deren Absenderprofil
* PDF-Generierung (mit Hinweiskasten „Diese Gutschrift bezieht sich auf Rechnung …“) und E-Mail-Versand

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

**Darstellung:** Pro Steuersatz eine Zeile „zzgl. 19 % MwSt. auf 600,00 €“. Gibt es nur einen Steuersatz, steht die Zeile ohne „auf …“. Das gilt für die drei PDF-Vorlagen und die drei Detailansichten.

```
Nettobetrag                          800,00 €
zzgl. 19 % MwSt. auf 600,00 €        114,00 €
zzgl.  7 % MwSt. auf 200,00 €         14,00 €
Gesamtbetrag                         928,00 €
```

---

### Kleinunternehmerregelung (§ 19 UStG)

nuvio unterstützt Kleinunternehmer, die keine Umsatzsteuer berechnen.

**Schalter:** Einstellungen → Steuer und Bank → Häkchen „Kleinunternehmer (§ 19 UStG)“. Der Schalter gilt für alle Absenderprofile gemeinsam.

**Merkfeld pro Dokument:** Angebote, Rechnungen und Gutschriften haben ein Feld `kleinunternehmer` (nicht im Formular bearbeitbar). Es wird **beim Anlegen** des Dokuments aus den Einstellungen übernommen und ändert sich danach nicht mehr, auch nicht beim erneuten Speichern. Ein späteres Umlegen des Schalters wirkt daher nur auf neue Dokumente; bereits erstellte Dokumente behalten ihre Steuerbehandlung und ihr Aussehen.

* Eine Rechnung, die aus einem Angebot entsteht, erhält den Stand zum Zeitpunkt der Umwandlung.
* Eine Gutschrift zu einer Rechnung übernimmt den Status der Rechnung; eine freie Gutschrift den aktuellen Stand der Einstellungen.
* Nach der Migration `0014` galten alle bereits vorhandenen Dokumente als „nicht Kleinunternehmer“.

**Wirkung bei aktivem Kleinunternehmer-Status:**

* Berechnung: Alle Positionen zählen mit Steuersatz 0, es gilt Netto = Brutto und MwSt. = 0. Der erfasste Preis ist der Rechnungsbetrag.
* PDF: Die Spaltenköpfe lauten „Einzelpreis“ und „Gesamtpreis“ (ohne „netto“). Die Zeilen „Nettobetrag“ und „zzgl. … % MwSt.“ entfallen, es bleibt nur der Gesamtbetrag (bei Gutschriften „Gutschriftbetrag“). Unter der Tabelle steht der Hinweis: „Der Auftragnehmer ist Kleinunternehmer im Sinne des § 19 UStG und stellt daher keine Umsatzsteuer in Rechnung.“
* Detailansichten: In den Dokumentdaten steht „Steuer: Kleinunternehmer“, die Summen-Karte zeigt nur den Gesamtbetrag samt Hinweis, in der Positionstabelle entfällt die MwSt.-Spalte.
* Formulare: Die Spalte heißt „Einzelpreis“ (statt „Brutto-Einzelpreis“), die MwSt.-Spalte ist per CSS ausgeblendet (die Werte werden weiter mitgesendet, haben aber keine Wirkung), über der Tabelle steht ein Hinweis auf die Endpreise.

**Hinweise:**

* Die Steuernummer muss auf der Rechnung stehen. Sie erscheint in der Fußzeile, die die Vorlage ohne Briefpapier selbst rendert. Mit hinterlegtem Briefpapier muss sie in dessen Fußzeile eingedruckt sein – das gilt für **jedes** Absenderprofil mit eigenem Briefpapier.
* Grenzen (seit 2025): 25.000 € Vorjahresumsatz und 100.000 € im laufenden Jahr. nuvio überwacht diese Grenzen nicht; der Schalter wird von Hand gesetzt. Die Anwendung der Regelung sollte mit dem Steuerberater abgestimmt sein.

---

### PDF-Layout (Angebote, Rechnungen, Gutschriften)

Die drei PDF-Vorlagen (`templates/angebote/pdf.html`, `rechnungen/pdf.html`, `gutschriften/pdf.html`) sind bewusst gleich aufgebaut. Das Rendern läuft für alle drei über `_dokument_pdf_rendern` in `views.py` (WeasyPrint, Seitennummern, Briefpapier-Hintergrund); Rechnungen mit Archiv-PDF werden über `_rechnung_pdf_bytes` ausgeliefert.

**Briefkopf und Adressfenster (nur Seite 1)**

Das Layout ist für Fensterumschläge ausgelegt, sodass ein Dokument auch als Brief verschickt werden kann. Annahme: Das Adressfenster liegt 49 mm von der Oberkante und 20 mm vom linken Rand und ist 45 mm hoch (DL-Standardumschlag).

| Element | Position (vom Blattrand) |
|---|---|
| Briefkopf links (Logo, Firmenname, Block) | links, ab 8 mm von oben; Firmenname und Block haben dieselbe Schrift (9,25 pt, Name fett) und keinen Abstand dazwischen |
| Logo-Fach rechts | feste Höhe (72 px) ab 8 mm von oben; bei Logo links steht dort „Briefkopf rechts“ |
| Titel („RECHNUNG“, „ANGEBOT“, „GUTSCHRIFT“) und Tabelle mit Nummer, Datum, Fälligkeit/Gültigkeit/Bezug | rechts unter dem Logo-Fach |
| „Seite x von y“ | direkt unter dieser Tabelle |
| Absenderzeile | 49–52 mm, 7 pt, unterstrichen, im Fenster direkt unter der Fensterkante |
| Empfängeradresse | ab 55 mm (3 mm unter der Absenderzeile), 10 pt, 85 mm breit, alle Zeilen gleiche Schrift |
| Betreffzeile | unterhalb des Briefkopfblocks (Block ist 96 mm hoch) |

* **Adresszeilen:** Firma, Ansprechpartner („Vorname Nachname“, ohne „z. Hd.“), Straße, PLZ Ort; das Land nur bei Auslandskunden, in Großbuchstaben (DE, Deutschland und Germany werden unterdrückt). Im Fenster ist Platz für etwa 6 Zeilen.
* **Betreffzeile:** Bei Rechnungen und Gutschriften ohne Präfix und komplett fett (13 px); bei Angeboten fett in 12 px.
* **Abstand zur Tabelle:** Zwischen Einleitungstext und Positionstabelle liegen 8 px.
* **Briefpapier:** Der Bereich des Adressfensters (etwa 45–95 mm Höhe, 20–110 mm Breite) muss im Hintergrund-PDF frei bleiben, ebenso der Briefkopfbereich, soweit nuvio selbst Logo und Blöcke druckt.
* **Seitennummer:** nuvio stempelt „Seite x von y“ mit ReportLab (`seitennummern_einstempeln`). Position auf Seite 1: `_rechnung_seite_y_erste(zeilen)` mit 4,9 mm je Zeile der Tabelle (Zeilenhöhe plus Tabellenabstand), kalibriert auf Baseline 56,3 mm bei drei Zeilen; auf Folgeseiten: `RECHNUNG_SEITE_Y_FOLGE` (12 mm von oben, rechtsbündig bei 190 mm). Ändert man in der Vorlage die Höhe des Kopfblocks, muss diese Kalibrierung angepasst werden.
* **Folgeseiten:** Sie haben keinen Briefkopf mehr, nur „Seite x von y“ oben rechts; der Inhalt beginnt direkt am Seitenrand von 20 mm. Das Briefpapier (eine Seite) wird auf allen Seiten untergelegt.

**Weitere Layout-Regeln**

* **Unterer Seitenrand:** Ist im Absenderprofil ein Hintergrund-PDF hinterlegt, gilt der dort eingestellte untere Rand (Standard 28 mm), damit Inhalte nicht in die Fußzeile des Briefpapiers laufen. Ohne Briefpapier sind es 10 mm, die Fußzeile rendert die Vorlage dann selbst (mit dem Firmennamen des Profils und den übrigen Daten aus den Einstellungen) und steht direkt unter dem Inhalt, nicht am Seitenende.
* **Summenblock:** Der Block mit Nettobetrag, MwSt.-Zeilen je Steuersatz und Gesamtbetrag (`tfoot` der Positionstabelle) ist als `display: table-row-group` mit `break-inside: avoid` gesetzt. Er erscheint nur einmal am Ende der Positionen und wird nicht auf jeder Seite wiederholt oder getrennt. Bei Kleinunternehmern besteht er nur aus dem Gesamtbetrag (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg)).
* **Hinweis „Fortsetzung auf Seite n“:** Bei mehrseitigen Dokumenten stempelt nuvio unten rechts ein kleines Etikett mit Pfeil auf jede Seite außer der letzten. Es wird nicht in den Vorlagen, sondern ebenfalls in `seitennummern_einstempeln` gezeichnet; Schrift 6,5 pt, Kästchenhöhe 12 pt, Abstand zur letzten Textzeile 5 mm. Der Textbereich über dem unteren Rand des Profils zählt dafür.

---

### E-Mail-Übergabe an Thunderbird

Der Button „Per E-Mail senden“ erzeugt das PDF, speichert es in den temporären Ordner und öffnet in Thunderbird ein neues Schreibfenster (`thunderbird -compose` mit `to`, `subject`, `body` als HTML, `attachment` und `preselectid`). Der Status wechselt wie bisher auf „Gesendet“, sobald die Übergabe geklappt hat; abgeschickt wird erst in Thunderbird.

* **Programm:** nuvio sucht `thunderbird.exe` im PATH und in den üblichen Installationsordnern (`Program Files`, `Program Files (x86)`, `%LOCALAPPDATA%\Programs`). Bei abweichendem Ort in `settings.py` setzen: `THUNDERBIRD_PFAD = r"D:\Apps\Thunderbird\thunderbird.exe"`.
* **Absenderadresse:** Im Absenderprofil die Thunderbird-Identität eintragen (z. B. `id2`). Die Nummer steht in Thunderbird unter Einstellungen → Konfigurationseditor: Suche nach „useremail“, Einträge der Form `mail.identity.id2.useremail`. Ohne Eintrag gilt die Standard-Identität.
* **Sonderzeichen:** Einfache Anführungszeichen im Betreff werden durch typografische ersetzt, der Text wird als HTML mit `<br>` übergeben. Dateinamen von Anhängen dürfen weder Komma noch Apostroph enthalten; sonst erscheint eine Fehlermeldung und der Status bleibt unverändert.
* **Fehler:** Wird Thunderbird nicht gefunden oder nicht gestartet, zeigt nuvio die Meldung an; der Status ändert sich dann nicht.

---

### Platzhalter-System

In den Einleitungs- und Schlusstexten von Angeboten und Rechnungen – sowohl direkt im Dokument als auch in den vorbelegten Standardtexten unter Einstellungen – können Platzhalter eingefügt werden, die beim PDF-Export automatisch durch echte Werte ersetzt werden. Über das Dropdown „Platzhalter einfügen…“ im Editor lassen sich folgende Variablen einfügen (Ausnahme: `{{rechnung_leistungsmonat}}`, siehe unten):

| Platzhalter | Ersetzt durch |
|---|---|
| `{{kunde_firma}}` | Firmenname des Kunden |
| `{{kunde_ansprechpartner}}` | Vor- und Nachname kombiniert |
| `{{kunde_vorname}}` | Nur Vorname des Kunden |
| `{{kunde_nachname}}` | Nur Nachname des Kunden |
| `{{kunde_ort}}` | Ort des Kunden |
| `{{angebot_nummer}}` | Angebotsnummer (nur in Angeboten) |
| `{{angebot_datum}}` | Angebotsdatum (nur in Angeboten) |
| `{{rechnung_nummer}}` | Rechnungsnummer (nur in Rechnungen) |
| `{{rechnung_datum}}` | Rechnungsdatum (nur in Rechnungen) |
| `{{rechnung_leistungsmonat}}` | Monat und Jahr des Rechnungsdatums, z. B. „Oktober 2026“ (nur in Rechnungen) |
| `---seitenumbruch---` | Erzwungener Seitenumbruch im PDF |

> **Hinweis:** `{{rechnung_leistungsmonat}}` ist noch nicht im Dropdown „Platzhalter einfügen…“ enthalten und muss vorerst von Hand eingetippt werden (siehe To do). In Gutschriften werden Platzhalter derzeit nicht ersetzt.

Die **E-Mail-Vorlagen** (Betreff und Text für Angebote, Rechnungen und Gutschriften) verwenden ein eigenes, kleineres Platzhalter-Set, das unabhängig vom oben genannten System funktioniert:

| Platzhalter | Ersetzt durch |
|---|---|
| `{{nummer}}` | Dokumentnummer |
| `{{kundenname}}` | Firmenname, sonst kombinierter Ansprechpartner |
| `{{firma}}` | „Firmenname im Dokument“ des Absenderprofils des Dokuments (leer: „Name“ aus den Stammdaten) |
| `{{datum}}` | Dokumentdatum |

> **Bekannte Einschränkung:** In den E-Mail-Vorlagen stehen `{{kunde_vorname}}` und `{{kunde_nachname}}` aktuell *nicht* getrennt zur Verfügung – nur das kombinierte `{{kundenname}}`. Eine Erweiterung ist möglich, aber noch nicht umgesetzt.

---

### Einstellungen

Alle zentralen Parameter der Anwendung werden einmalig in den Einstellungen hinterlegt:

**Stammdaten**

* Name, Zusatzzeilen (z. B. Berufsbezeichnung, Registernummer), Adresse, Telefon, E-Mail, Website
* Logo und Briefpapier werden **nicht** mehr hier, sondern pro Rolle in den Absenderprofilen festgelegt. Die Stammdaten dienen als Rückfallwert (Name) und für die Fußzeile ohne Briefpapier.

**Steuer und Bank**

* Steuernummer, USt-IdNr., Bankverbindung (IBAN, BIC)
* Schalter „Kleinunternehmer (§ 19 UStG)“ (siehe [Kleinunternehmerregelung](#kleinunternehmerregelung--19-ustg))

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

**Absenderprofile**

* Karte mit Link zur Profilverwaltung (siehe [Absenderprofile](#absenderprofile-rollen))

**Datensicherung**

* ZIP-Download mit der Datenbank und allen hochgeladenen Dateien (Logo, Briefpapier, E-Mail-Anhänge, archivierte Rechnungs-PDFs)

---

## Technischer Stack

* **Backend:** Python / Django
* **Datenbank:** SQLite (lokal, keine externe Datenbank nötig)
* **PDF-Generierung:** WeasyPrint + pypdf (Hintergrundmerge, Seitennummern mit ReportLab)
* **E-Mail-Versand:** Übergabe an Mozilla Thunderbird über die Kommandozeile (`thunderbird -compose`), die Absenderadresse richtet sich nach der Thunderbird-Identität des Absenderprofils
* **Frontend:** HTML/CSS (eigene Templates, ohne JavaScript-Framework; kleine Inline-Skripte, z. B. für das Auf-/Zuklappen der Bundle-Unterartikel und für die Positionszeilen in den Formularen)
* **Betrieb:** Lokaler Django-Entwicklungsserver, Start per `start.bat` (Windows)

---

## Installation und Start

### Voraussetzungen

* Python 3.x
* Virtuelle Umgebung mit installierten Abhängigkeiten (`pip install -r requirements.txt`)
* WeasyPrint (für PDF-Erzeugung, optional, aber empfohlen)
* Mozilla Thunderbird (für den E-Mail-Versand aus der App)

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

Anschließend unter `http://127.0.0.1:8000` mit den gewählten Zugangsdaten anmelden und die Einstellungen aufrufen, um Stammdaten, Nummernkreise und E-Mail-Vorlagen einzurichten. Danach unter „Absenderprofile“ Logo, Briefkopf und Briefpapier pro Rolle festlegen.

### Nach Änderungen am Datenmodell

Nach Änderungen an `models.py` immer `makemigrations` und `migrate` ausführen und vorher eine Datensicherung anlegen. Mit `makemigrations --check` lässt sich prüfen, ob Modelle und Migrationen übereinstimmen („No changes detected“).

---

## Authentifizierung

nuvio ist durch eine einfache Benutzeranmeldung geschützt. Alle Seiten der Anwendung sind nur nach erfolgreicher Anmeldung erreichbar.

* Der Login erfolgt über `/login/`
* Die Abmeldung ist jederzeit über den „Abmelden“-Link in der Seitenleiste möglich
* Benutzerverwaltung (weitere Nutzer anlegen, Passwörter ändern) über das Django-Admininterface unter `/admin/`

---

## Projektstruktur

```
nuvio/
├── core/                    # Hauptmodul: Models, Views, Forms, URLs
│   ├── models.py            # Datenmodell (Kunden, Artikel, Bundles, Absenderprofile, Angebote, Rechnungen, Gutschriften, SummenMixin)
│   ├── views.py             # Alle Ansichten und PDF-/E-Mail-Logik (u. a. _dokument_pdf_rendern, Rechnungs-Archiv)
│   ├── forms.py             # Django-Formulare und Formsets
│   ├── admin.py             # Admin-Registrierung (u. a. Absenderprofil)
│   ├── middleware.py        # Login-Schutz für alle Seiten
│   ├── templatetags/
│   │   └── nuvio_filters.py # Eigene Template-Filter (Datum, Euro, Platzhalter-Ersetzung)
│   └── migrations/          # Datenbankmigrationen (0015 Absenderprofil/Sperre, 0016 Angebote, 0017 Gutschriften, 0018 Thunderbird-Identität)
├── rechnungssystem/         # Django-Projektkonfiguration
│   ├── settings.py          # Entwicklungseinstellungen
│   ├── settings_prod.py     # Produktionseinstellungen
│   └── urls.py              # URL-Konfiguration inkl. Login/Logout
├── templates/               # HTML-Templates (Dashboard, Listen, Formulare, PDFs, E-Mails)
│   ├── angebote/, rechnungen/, gutschriften/   # u. a. Detail, Formular, PDF
│   ├── absenderprofile/     # Liste, Formular, Löschen
│   └── login.html           # Anmeldeseite im Nuvio-Design
├── media/                   # Hochgeladene Dateien
│   ├── logo/                # Logos der Absenderprofile
│   ├── hintergrund/         # Briefpapier (PDF) der Absenderprofile
│   └── rechnungen_archiv/   # Archivierte PDFs gesperrter Rechnungen
├── manage.py                # Django-Management-Utility
└── start.bat                # Schnellstart für Windows
```

---

## Letzte Änderungen (5. November 2026)

* **Absenderprofile:** Neues Modell `Absenderprofil` (Logo, Briefkopf links/rechts, Absenderzeile, Briefpapier, unterer Rand, Thunderbird-Identität) für Rollen mit gemeinsamem Nummernkreis, kein Mandant. Fremdschlüssel an Rechnung (`0015`), Angebot (`0016`) und Gutschrift (`0017`); Angebot → Rechnung und Rechnung → Gutschrift reichen das Profil weiter. Verwaltung unter Einstellungen → Absenderprofile; Logo und Hintergrund-PDF sind aus den Stammdaten entfernt, die Migration hat die bisherigen Werte in das Profil „Standard“ übernommen.
* **Neues PDF-Layout:** Briefkopf aus dem Profil, Empfängeradresse im Fenster ab 55 mm mit Absenderzeile (49–52 mm), Titel und Nummer/Datum-Tabelle rechts unter dem Logo, „Seite x von y“ unter dieser Tabelle, keine Kopfzeile auf Folgeseiten. Gleiche Gestaltung für Angebote, Rechnungen und Gutschriften; „Rechnung an“, „z. Hd.“ und das Land „DE“ entfallen, die Betreffzeile steht ohne „Objekt:“ fett.
* **GoBD-Sperre für Rechnungen:** Ab „Bezahlt“ unveränderbar (`gesperrt_am`), mit archiviertem PDF (`pdf_archiv`); Statuswechsel durch Gutschriften bleiben möglich. Der Zahlungseingang rechnet mit dem offenen Betrag inklusive Gutschriften.
* **Standardtexte im Formular:** Einleitung, Schluss und Zahlungsbedingungen (bzw. Einleitung und Schluss bei Angeboten) sind beim Anlegen vorbelegt.
* **E-Mail-Versand nur noch über Thunderbird:** Die Übergabe an Outlook (COM, `pywin32`) ist entfernt. nuvio öffnet ein Thunderbird-Schreibfenster mit Empfänger, Betreff, Text und Anhängen; die Absenderadresse wählt die Thunderbird-Identität des Absenderprofils (Migration `0018`, ersetzt das Feld „Absender-E-Mail“). `{{firma}}` richtet sich weiter nach dem Absenderprofil.
* **Einstellungen:** „Firmendaten“ heißt jetzt „Stammdaten“ (Feld „Name“), die Karte „Absenderprofile“ steht weiter unten.
* **PDF-Erzeugung vereinheitlicht:** Gemeinsame Funktion `_dokument_pdf_rendern` für Angebote, Rechnungen und Gutschriften (Ansicht und E-Mail).

### Davor (3. November 2026)

* **Summenblock nach Steuersätzen:** Eine MwSt.-Zeile je Steuersatz mit Bemessungsgrundlage in den drei PDF-Vorlagen und den drei Detailansichten (vorher wurde nur der Satz der ersten Position ausgewiesen). Die Berechnung läuft gemeinsam über `SummenMixin` aus der Brutto-Summe je Satz; `Netto + MwSt. = Brutto` gilt jetzt auch bei Gutschriften immer.
* **Kleinunternehmerregelung:** Neuer Schalter in den Einstellungen, Merkfeld `kleinunternehmer` pro Angebot, Rechnung und Gutschrift (beim Anlegen festgehalten), Gutschrift übernimmt den Status der Rechnung. PDF-Vorlagen, Detailansichten und Formulare passen sich an (nur Gesamtbetrag, Hinweis auf § 19 UStG, MwSt.-Spalte im Formular ausgeblendet).
* **Migration `0014`:** Enthält die vier neuen Felder `kleinunternehmer` sowie nachgeholte Modelländerungen (entfernte Felder `bezahlt_am`, `bezahlt_betrag` und `vorlage` an der Rechnung, kleinere Feldanpassungen).
* **Rechnungs-Detailansicht:** Status-Badge zeigt den Status wieder im Badge, die Abfrage des nicht mehr vorhandenen Felds `bezahlt_am` ist entfernt.
* **PDF-Hinweis „Fortsetzung auf Seite n“:** Dezenter gestaltet (kleinere Schrift, kleineres Kästchen und kleinerer Pfeil).

### Davor (2. November 2026)

* **Artikelübersicht:** Bundle-Unterartikel eingerückt und standardmäßig eingeklappt (Pfeil-Button), „Bundle“-Badge, kräftigere Trennlinie zwischen Haupt-Artikeln, `prefetch_related` in `artikel_liste`.
* **PDF-Seitenumbruch:** Unterer Seitenrand bei Briefpapier 28 mm, damit der Summenblock nicht mehr in die Fußzeile läuft (Angebote, Rechnungen, Gutschriften).
* **PDF-Summenblock:** Nettobetrag/MwSt./Gesamtbetrag erscheinen nur einmal am Ende der Positionstabelle (`display: table-row-group`) statt auf jeder Seite.
* **PDF-Kopfzeile:** Zusätzlicher Abstand unter der Kopfzeile, damit die Seitennummer nicht auf der Tabellenkopfzeile sitzt (inzwischen durch das Briefkopf-Layout ersetzt).
* **Leistungszeitraum:** Neuer Platzhalter `{{rechnung_leistungsmonat}}` (ohne neues Datenbankfeld) für die vereinfachte Angabe des Leistungsmonats auf Rechnungen.

---

## To do

Reihenfolge nach Priorität. Reverse Charge ist für uns nicht relevant und wird nicht umgesetzt.

### 1. Unveränderbarkeit (GoBD) – Rest

Umgesetzt: Rechnungen sind ab „Bezahlt“ gesperrt und archiviert (siehe [Unveränderbarkeit (GoBD)](#rechnungen)). Offen:

* Konzept mit dem Steuerberater abstimmen: Reicht die Sperre erst ab „Bezahlt“, oder sollen versendete Rechnungen ebenfalls gesperrt werden? Bis zur Zahlung ist eine versendete Rechnung änderbar, und das ausgelieferte PDF kann dann von dem abweichen, was der Kunde erhalten hat. Eine Möglichkeit wäre, das PDF schon beim Versand zu archivieren.
* Sollen „Storniert“ und versendete Gutschriften ebenfalls gesperrt werden (Storniert ist heute nicht gesperrt)? Versendete Rechnungen sollten storniert statt gelöscht werden, damit der Nummernkreis nachvollziehbar bleibt (ein Lösch-View für Rechnungen existiert nicht).
* Interne Notizen einer gesperrten Rechnung sind auf Modellebene änderbar, haben aber noch keine Oberfläche.

### 2. Bessere Wartbarkeit (doppelter Code)

* Gemeinsames Basis-Template für die drei PDF-Vorlagen (`{% extends %}` mit Blöcken für Titel, Meta-Tabelle, Empfänger, Schlusstext), damit Layoutänderungen nur einmal nötig sind. Der neue Briefkopf, die Adress- und die Steuerzeilen-Logik stecken inzwischen in je drei PDF-, Detail- und Formularvorlagen (gemeinsame Includes würden das vereinfachen).
* Die alten, nicht mehr benutzten Hilfsfunktionen `_seiten_y` und `_seiten_y_gutschrift` in `views.py` entfernen.
* Automatische Tests für Summenberechnung (gemischte Steuersätze, Kleinunternehmer, Cent-Rundung), offenen Betrag, Gutschriften-Verrechnung, Nummernkreise, das Merkfeld `kleinunternehmer`, die Sperrlogik (`gesperrt_am`) und das Profil-Handling.

### 3. Dokument duplizieren

* Funktion „Kopie erstellen“ für Angebote und Rechnungen (Positionen, Texte, Kunde und Absenderprofil übernehmen; neue Nummer, Status `Entwurf`, aktuelles Datum). Der Kleinunternehmer-Status der Kopie folgt dabei dem aktuellen Stand der Einstellungen.

### Weitere offene Punkte

* **Bundle-Preis:** Der Preis eines Bundles soll berechnet statt gespeichert werden (Summe aus Menge × Einzelpreis der Unterartikel, Property am Artikel; Formularfeld bei Bundles ausblenden, inaktive Unterartikel klären).
* Absenderprofile: Beim Ersetzen von Logo oder Briefpapier gibt es keinen Weg, die Datei ersatzlos zu entfernen (z. B. Link „Logo entfernen“). Optional eigene Standardtexte je Profil.
* Die ungenutzten Felder `logo` und `hintergrund_pdf` am Modell `Einstellungen` per Migration entfernen.
* Fußzeile ohne Briefpapier am Seitenende verankern statt direkt unter dem Inhalt.
* Probedruck des Adressfensters auf einem echten Umschlag (Annahme: Fenster 49 mm von oben, 20 mm von links, 45 mm hoch); optional Falzmarken bei 105 mm und 210 mm.
* Steuerhinweis bei 0 %-Positionen (Freitext, z. B. Befreiungsgrund): bisher nur über den Schlusstext möglich, ggf. später eigenes Feld.
* Kleinunternehmer-Hinweistext ist fest in den PDF-Vorlagen hinterlegt; ggf. in den Einstellungen editierbar machen.
* Gutschrift von Hand anlegen und im Formular eine Rechnung wählen: Das Formular zeigt den Hinweis zunächst nach dem aktuellen Stand der Einstellungen, gespeichert wird der Status der Rechnung; das Profil bleibt der Formularauswahl entsprechend (nicht automatisch das der gewählten Rechnung).
* Rechnungs-Detailansicht: Datum der letzten Zahlung in den Rechnungsdaten anzeigen (optional, als Eigenschaft aus den Zahlungen).
* Platzhalter `{{rechnung_leistungsmonat}}` im Dropdown „Platzhalter einfügen…“ ergänzen (Rechnungsformular und Einstellungen).
* Bundle-Artikel auch in Rechnungen und Gutschriften einfügbar machen (aktuell nur in Angeboten).
* `{{kunde_vorname}}` und `{{kunde_nachname}}` in den E-Mail-Vorlagen ergänzen.
