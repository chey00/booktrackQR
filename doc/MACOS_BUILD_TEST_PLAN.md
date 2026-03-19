# macOS Test-Build Vorbereitung (PyInstaller)

## Ziel
Erste, minimale Testbasis für einen PyInstaller-basierten macOS-`.app` Build der Haupt-App.
Keine Ausführung, keine `.app`/`.dmg` Erstellung, keine Produktiv-Konfiguration.

## Einstiegspunkt
- Haupt-Einstiegspunkt: `src/main.py`

## Benötigte Python-Abhängigkeiten (erkennbar im Projekt)
Pflicht für Haupt-App:
- `PyQt6`
- `pymysql`
- `python-dotenv`

QR-Logik (nur falls QR-Generierung aktiv genutzt wird):
- `qrcode`
- (implizit) `Pillow` als qrcode-Backend

QR-Scanner (nicht Priorität, nur falls eingebunden):
- `opencv-python` (`cv2`)
- `mysql-connector-python`

Optional (nur für Excel-Import in Schülerverwaltung):
- `pandas`
- `openpyxl`

## Benötigte Ressourcen (Data-Files)
Für den ersten Test-Build der Haupt-App:
- `pic/` (Bilder/Icons für UI)

Optional für Tests:
- `src/qr_generation/` (Code ist ohnehin gebundelt, kein Data-File)
- `src/QR/` **nicht erforderlich** (Produktiv speichert nicht im Bundle)

Nicht zwingend im ersten Test-Build:
- `db/` (SQL/PDF Doku)
- `doc/` (Doku)
- `schuelerlisten/`

## Konfigurationsdatei (.env)
- `.env` wird **nicht** im Repository gespeichert.
- `.env` wird **nicht** im PyInstaller-Bundle enthalten.
- `.env` muss manuell im User-Data-Ordner bereitgestellt werden:
  - `~/Library/Application Support/BooktrackQR/.env`
- Ohne `.env` ist kein Start möglich (bewusste Sicherheitsentscheidung).

## Minimaler PyInstaller-Vorschlag (nicht ausführen)
Beispiel für eine erste Test-CLI:
```bash
cd <lokaler-repo-ordner>
pyinstaller \
  --windowed \
  --name BooktrackQR \
  --paths src \
  --add-data "pic:pic" \
  src/main.py
```

Hinweis:
- `--paths src` stellt sicher, dass `src/` im Importpfad liegt.
- `--add-data "pic:pic"` erwartet, dass im Bundle `pic/` auf Root-Ebene liegt.

## Minimaler Spec-Hinweis (optional, nicht erstellt)
Falls ein Spec gewünscht ist:
- `Analysis(..., pathex=['src'], datas=[('pic', 'pic')], ...)`
- Entry: `src/main.py`

## Vorbereitung vor dem ersten Start
1. App installieren/entpacken (Test-Build).
2. Ordner anlegen:
   - `~/Library/Application Support/BooktrackQR`
3. `.env` Datei dort ablegen:
   - `~/Library/Application Support/BooktrackQR/.env`

Optional: Beispielinhalt für `.env` (ohne echte Zugangsdaten):
```
DB_HOST=192.168.x.x
DB_PORT=xxxx
DB_NAME=xxxxxxxx
DB_USER=xxxxxxxx
DB_PASSWORD=*** 
DB_CONNECT_TIMEOUT=20
```

Wichtig:
- `.env` wird **nicht** gebundelt und **nicht** im Repository gespeichert.
- Die App erwartet die `.env` im User-Data-Ordner.
- Ohne `.env` ist kein Start möglich (bewusste Sicherheitsentscheidung).

## macOS Besonderheiten
- Keine Signierung/Notarisierung (explizit ausgeschlossen).
- Schreibpfade sind bereits aus dem Bundle ausgelagert:
  - `~/Library/Application Support/BooktrackQR`
- Falls QR-Scanner später genutzt wird:
  - Kamera-Berechtigung in `Info.plist` nötig (nicht Bestandteil dieses Test-Plans).

## Risiken beim ersten Testlauf
- Fehlende Abhängigkeiten, da es kein `requirements.txt`/`pyproject.toml` gibt.
- Falls `.env` nicht im User-Data-Ordner liegt, startet die App nicht.
- QR-Scanner kann zusätzliche native Abhängigkeiten benötigen (OpenCV).
- Excel-Import benötigt `pandas`/`openpyxl`, falls genutzt.

## Abgrenzung (nicht enthalten)
- Keine finale `.dmg` Lösung
- Keine Signierung/Notarisierung
- Kein finaler Packaging-Workflow
- Keine vollständige Dependency-Definition
