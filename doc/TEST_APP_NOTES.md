# BooktrackQR macOS Test-Setup Hinweise

Diese Notiz beschreibt die minimalen Anpassungen, damit die App als macOS `.app` testbar gebündelt werden kann.

## Ressourcenpfade
- Bilder (`pic/`) und die `.env` werden über `src/app_paths.py` aufgelöst.
- Die App versucht zuerst die gebündelten Ressourcen zu nutzen.
- Im Entwicklungsmodus wird bei Bedarf auf die Projektstruktur (`../pic`, `src/.env`) zurückgefallen.

## Schreibpfade
- Schreibzugriffe gehen in den User-Ordner:
  - `~/Library/Application Support/BooktrackQR`
- Dort liegen z. B.:
  - `QR/counters.json` (QR-Zähler)
  - `QR/images/*.png` (Test-QR-Bilder)
  - `scan_historie.csv` (Scanner-Log)

Optional kann der Pfad über `BOOKTRACKQR_DATA_DIR` überschrieben werden.

## .env
- Erwartet wird eine `.env` entweder im Bundle (für Tests) oder in
  `~/Library/Application Support/BooktrackQR/.env`.

## QR-Scanner (nachrangig)
- Der Scanner ist nicht Teil des Standard-Starts.
- Für echten Scanner-Betrieb in einer `.app` sind Kamera-Berechtigungen in der Info.plist nötig.
