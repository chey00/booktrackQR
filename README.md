**Schulbibliothek – Ausleihe mit iPad, Raspberry Pi & QR-Codes**

**Zweck des Systems**

Dieses System dient der **einfachen, schnellen und fehlerfreien Verwaltung von Schulbuch-Ausleihen**.
Lehrkräfte können Bücher und Schüler verwalten, Ausleihen durchführen und Rückgaben verbuchen – **ohne Zettelwirtschaft und ohne manuelle Listen**.

Die Bedienung erfolgt über ein **iPad**, die Daten werden zentral auf einem **Raspberry Pi** gespeichert. Jedes Buch wird eindeutig über einen **QR-Code** identifiziert.

**Gesamtfunktion**

Das System bildet den kompletten Ausleih-Workflow ab:

* Anlegen und Verwalten von **Büchern, Schülern, Klassen und Schuljahren**
* **Zentrale Speicherung** aller Daten in einer Datenbank
* **Ausleihe und Rückgabe per QR-Scan**, ohne Tippen
* Klare **Validierungen und Fehlermeldungen**, um falsche Eingaben zu verhindern

Ziel ist ein **robuster Alltagsbetrieb im Schulumfeld**: schnell, nachvollziehbar und wartbar.

**Systemübersicht**

**Backend / Datenbank**

* Läuft auf einem **Raspberry Pi im Schulnetz**
* Stellt einen Datenbankdienst bereit
* Speichert:
  + Schüler
  + Bücher
  + Klassen
  + Schuljahre
  + Ausleihen
* Verhindert logisch falsche Zustände (z. B. ein Buch gleichzeitig an zwei Schüler)

**Datenmodell (fachlich)**

* **Schüler**
  + Vorname, Nachname, Klasse, Status (aktiv/inaktiv)
  + Liste aktuell ausgeliehener Bücher
* **Buch**
  + Titel, Verlag, Auflage
  + Anzahl der vorhandenen Exemplare
* **Ausleihe**
  + Verknüpft Schüler ↔ Buch
  + Stellt sicher: Ein Exemplar kann nur einmal ausgeliehen sein
* **Klasse / Schuljahr**
  + Strukturierung und Filterung für den Schulalltag

**iPad-GUI**

* **Startseite mit klaren Hauptfunktionen**
* Verwaltungsansichten für:
  + Bücher
  + Schüler
  + Klassen
  + Schuljahre
* Suchen und Filtern nach relevanten Kriterien
* Pflichtfelder werden erzwungen, fehlerhafte Eingaben blockiert

**QR-Code-Funktionalität**

* Für jedes Buch wird ein **eindeutiger QR-Code** erzeugt
* QR-Codes werden als **Etiketten gedruckt** und auf die Bücher geklebt
* Die iPad-Kamera scannt den Code:
  + bei **Ausleihe**
  + bei **Rückgabe**
* Das System erkennt:
  + ungültige Codes
  + unbekannte Bücher
  + bereits ausgeliehene Exemplare

**Fehlerverhalten (bewusst eingeplant)**

Das System ist so ausgelegt, dass typische Fehler **klar abgefangen** werden:

* Fehlende Pflichtfelder → Speichern nicht möglich, verständlicher Hinweis
* Bereits ausgeliehenes Buch → Warnung mit aktuellem Entleiher
* Backend kurzzeitig nicht erreichbar → erneuter Ladeversuch möglich
* Ungültiger QR-Code → erneutes Scannen ohne Folgeschäden

**Zielnutzen**

* **Zeitersparnis** im Schulalltag
* **Keine doppelten Ausleihen**
* **Nachvollziehbarkeit**, wer welches Buch hat
* **Einfache Bedienung**, auch unter Zeitdruck
* **Zentrale Datenhaltung** statt Excel oder Papierlisten

**Aktueller Stand (macOS Testbuild)**

* App wurde erfolgreich als macOS `.app` gebaut
* `.dmg` wurde erstellt und getestet
* App kann installiert und gestartet werden
* Interne Testverteilung ist möglich

**Installation (macOS)**

1. `.dmg` öffnen
2. App per Drag & Drop nach „Applications“ ziehen
3. App aus „Applications“ starten

Hinweis: App nicht direkt aus dem DMG starten.

**Wichtige Voraussetzung: `.env`**

Die `.env` wird **nicht** mitgeliefert und **nicht** im Repository gespeichert.  
Sie muss manuell erstellt werden unter:

`~/Library/Application Support/BooktrackQR/.env`

Beispiel:
```
DB_HOST=192.168.10.195
DB_PORT=3306
DB_NAME=booksdb
DB_USER=booksuser
DB_PASSWORD=Fswi-2!
DB_CONNECT_TIMEOUT=20
```

Ohne `.env` startet die App nicht.  
Dies ist eine bewusste Sicherheitsentscheidung.

**Erster Start unter macOS**

* App ist aktuell **nicht signiert** und **nicht notarisiert**
* macOS kann beim ersten Start eine Sicherheitswarnung anzeigen
* Lösung:
  Rechtsklick auf die App → „Öffnen“ → Bestätigen

**Aktuelle Einschränkungen**

* keine Code-Signierung
* keine Notarization
* `.env` muss manuell erstellt werden
* QR-Druckfunktion ist aktuell nur Stub
* QR-Scanner ist nachrangig

**Hinweis für Entwickler**

* Projekt kann weiterhin lokal über Python gestartet werden
* Build erfolgt über PyInstaller
* `.dmg` wird über Script erstellt: `scripts/create_dmg.sh`
