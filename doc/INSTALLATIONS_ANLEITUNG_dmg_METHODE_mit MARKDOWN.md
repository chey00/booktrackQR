# Anleitung: macOS App als .dmg erstellen (einfach erklärt)

## Ziel
Diese Anleitung zeigt Schritt für Schritt, wie unsere App als `.dmg`-Datei erstellt wird.

## Voraussetzungen
- MacBook
- Python installiert
- Projekt vorhanden

## Schritt 1: PyInstaller installieren
```
pip install pyinstaller
```

## Schritt 2: App erstellen
```
pyinstaller --onefile --windowed main.py
```

## Schritt 3: .dmg erstellen
```
hdiutil create -volname "MeineApp" -srcfolder dist/MeineApp.app -ov -format UDZO MeineApp.dmg
```

## Schritt 4: Installation
1. .dmg öffnen
2. App in Programme ziehen
3. Starten

## Hinweis
Beim ersten Start kann eine Sicherheitswarnung erscheinen.
