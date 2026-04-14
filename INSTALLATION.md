# BooktrackQR – Installation (macOS)

## Installation

1. ZIP entpacken
2. DMG öffnen
3. App in Programme ziehen
4. App starten

---

## Wichtige Hinweise

Die App benötigt eine .env Datei unter:

~/Library/Application Support/BooktrackQR/.env

---

## Probleme & Lösungen

### App kann nicht geöffnet werden

Rechtsklick → Öffnen

oder im Terminal:

xattr -cr /Applications/BooktrackQR.app

---

### Kamera funktioniert nicht

tccutil reset Camera

App neu starten

---

### .env fehlt

mkdir -p ~/Library/Application\ Support/BooktrackQR
nano ~/Library/Application\ Support/BooktrackQR/.env

---

### Keine Verbindung zur Datenbank

- falsche IP
- nicht im Schulnetz
