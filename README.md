# UPDATE// 24.03.26 // Denis
# BooktrackQR – Schulbibliothekssystem

> ⚠️ Hinweis:  
> Dies ist aktuell eine **Testversion für interne Nutzung**.

## Aktuelle Version

Version: V1.X

Die Versionsnummer wird beim Release automatisch aktualisiert.

## Projektbeschreibung

Dieses System dient der **einfachen, schnellen und fehlerfreien Verwaltung von Schulbuch-Ausleihen**.

Lehrkräfte können Bücher und Schüler verwalten, Ausleihen durchführen und Rückgaben verbuchen –  
**ohne Zettelwirtschaft und ohne manuelle Listen**.

Die Anwendung läuft als **macOS Desktop-App**.  
Die Daten werden zentral auf einem **Raspberry Pi (Datenbankserver)** gespeichert.  
Jedes Buch wird eindeutig über einen **QR-Code** identifiziert.

---

## Gesamtfunktion

Das System bildet den kompletten Ausleih-Workflow ab:

- Verwaltung von **Büchern, Schülern, Klassen und Schuljahren**
- **Zentrale Datenhaltung** in einer Datenbank
- **Ausleihe und Rückgabe per QR-Code**
- Validierungen zur Vermeidung von Fehlern

Ziel ist ein **robuster, schneller und nachvollziehbarer Schulbetrieb**.

---

## Systemübersicht

### Backend / Datenbank

- Läuft auf einem **Raspberry Pi im Schulnetz**
- Stellt den Datenbankdienst bereit
- Speichert:
  - Schüler
  - Bücher
  - Klassen
  - Schuljahre
  - Ausleihen

---

### macOS App (GUI)

- Desktop-Anwendung für macOS
- Zentrale Steuerung aller Funktionen
- Verwaltungsansichten für:
  - Bücher
  - Schüler
  - Klassen
  - Schuljahre
- Such- und Filterfunktionen
- Eingabevalidierung

---

### QR-Code-Funktionalität

- Jedes Buch erhält einen **eindeutigen QR-Code**
- QR-Codes werden gedruckt und auf Bücher geklebt
- Verwendung:
  - Ausleihe
  - Rückgabe

---

## Aktueller Stand (macOS Testbuild)

- ✅ App wurde erfolgreich als `.app` gebaut
- ✅ `.dmg` wurde erstellt und getestet
- ✅ Installation über Drag & Drop möglich
- ✅ App läuft unabhängig vom Projektordner
- ✅ Interne Testverteilung funktioniert

---

## Installation (macOS)

1. `.dmg` öffnen  
2. `BooktrackQR.app` in den Ordner **Programme** ziehen  
3. App aus **Programme** starten  

⚠️ Wichtig:  
App **nicht direkt aus dem DMG starten**.

---

## Wichtige Voraussetzung: `.env`

Die Anwendung benötigt eine `.env` Datei mit den Datenbank-Zugangsdaten.

📍 Speicherort:

~/Library/Application Support/BooktrackQR/.env

Beispiel: 

DB_HOST=192.168.xx.xxx
DB_PORT=xxxx
DB_NAME=xxxxxxx
DB_USER=xxxxxxxx
DB_PASSWORD=***
DB_CONNECT_TIMEOUT=20

❗ Wichtig:
- `.env` ist **nicht im Repository enthalten**
- `.env` ist **nicht im App-Bundle enthalten**
- Ohne `.env` startet die App **nicht**

👉 Das ist eine **bewusste Sicherheitsentscheidung**

---

## Erster Start unter macOS

Da die App aktuell nicht signiert ist, kann eine Warnung erscheinen:

👉 Lösung:
- Rechtsklick auf die App  
- „Öffnen“ auswählen  
- Bestätigen  

---

## Aktuelle Einschränkungen

- Keine Code-Signierung
- Keine Notarization
- `.env` muss manuell erstellt werden
- QR-Druckfunktion ist aktuell nur Stub
- QR-Scanner ist nachrangig

---


## Hinweis für Entwickler

Im Entwicklungsmodus kann die `.env` alternativ unter folgendem Pfad liegen:

  src/.env

Dies ist jedoch **nur für lokale Tests gedacht** und wird in der gebauten App nicht verwendet.


### Lokaler Start

  python src/main.py
  
### Build

  pyinstaller ....

### DMG Erstellung

  ./scripts/create_dmg.sh

---

## Ziel des Projekts

- Zeitersparnis im Schulalltag
- Vermeidung doppelter Ausleihen
- Klare Nachvollziehbarkeit
- Einfache Bedienung
- Zentrale Datenhaltung

---

## Release (macOS Testversion)

Neue Version erstellen mit:

release

oder:

./scripts/release_dmg.sh

Das Script:
- prüft Git-Status
- baut die App
- erstellt die .dmg
- versieht sie mit Version

Voraussetzungen:
- .venv vorhanden
- .env vorhanden unter:
  ~/Library/Application Support/BooktrackQR/.env

Ergebnis:
- fertige .dmg im dist/ Ordner
