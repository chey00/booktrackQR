#!/usr/bin/env bash
# =========================================================
# BooktrackQR – Release Script (macOS DMG Build)
# =========================================================
# VOR DEM START (einmalig oder bei Änderungen):
# 1) Terminal öffnen
# 2) In den Projektordner wechseln:
#    cd /Users/neo/projects/python/booktrackQR
# 3) (Optional) .venv erstellen, falls nicht vorhanden:
#    python3 -m venv .venv
# 4) (Optional) Abhängigkeiten installieren:
#    source .venv/bin/activate
#    pip install -r requirements.txt   # falls vorhanden
#    pip install pyinstaller          # falls nicht installiert
#
# SCRIPT AUSFÜHREN:
#    ./scripts/release_dmg.sh
#    ODER (nach erstem Lauf):
#    release
#
# NACH DEM LAUF:
# - Ergebnis prüfen:
#    ls -lh dist/BooktrackQR_V1.*.dmg
# - DMG testen:
#    open dist/BooktrackQR_V1.<VERSION>.dmg
# - Optional Commit & Push (falls Änderungen am Repo):
#    git status
#    git add .
#    git commit -m "Release V1.<VERSION>"
#    git push origin main
#
# HINWEISE:
# - VERSION wird aktuell manuell gesetzt (siehe unten)
# - .env muss vorhanden sein unter:
#   ~/Library/Application Support/BooktrackQR/.env
# - Ohne .env startet die App nicht
# =========================================================
set -e

VERSION="1.6"

PROJECT_DIR="$(pwd)"
VENV_PATH="${PROJECT_DIR}/.venv"
APP_PATH="${PROJECT_DIR}/dist/BooktrackQR.app"
DMG_PATH="${PROJECT_DIR}/dist/BooktrackQR.dmg"
DMG_RENAMED_PATH="${PROJECT_DIR}/dist/BooktrackQR_V1.${VERSION}.dmg"

echo "[INFO] Release gestartet"
echo "[INFO] Projektordner: ${PROJECT_DIR}"

if [[ ! -d "${VENV_PATH}" ]]; then
  echo "[ERROR] Virtuelle Umgebung nicht gefunden: ${VENV_PATH}"
  exit 1
fi

echo "[INFO] Virtuelle Umgebung aktivieren"
source "${VENV_PATH}/bin/activate"

# One-Command Alias Setup (einmalig)
ALIAS_NAME="release"
SCRIPT_PATH="${PROJECT_DIR}/scripts/release_dmg.sh"
SHELL_RC="${HOME}/.zshrc"

if ! grep -q "alias ${ALIAS_NAME}=" "${SHELL_RC}" 2>/dev/null; then
  echo "[INFO] Erstelle One-Command Alias: ${ALIAS_NAME}"
  echo "alias ${ALIAS_NAME}='${SCRIPT_PATH}'" >> "${SHELL_RC}"
  echo "[INFO] Alias wurde in ${SHELL_RC} gespeichert"
  echo "[INFO] Bitte Terminal neu starten oder 'source ~/.zshrc' ausführen"
else
  echo "[INFO] Alias '${ALIAS_NAME}' existiert bereits"
fi

echo "[INFO] Git Safety Check"

# 1) Lokale Änderungen prüfen (dirty working tree)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "[ERROR] Lokale Änderungen vorhanden. Bitte committen oder verwerfen."
  git status
  exit 1
fi

# 2) Remote-Daten aktualisieren
git fetch origin

# 3) Prüfen ob Branch hinter origin/main ist
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)
BASE_HASH=$(git merge-base HEAD origin/main)

if [[ "$LOCAL_HASH" != "$REMOTE_HASH" ]]; then
  if [[ "$LOCAL_HASH" == "$BASE_HASH" ]]; then
    echo "[ERROR] Lokaler Branch ist nicht aktuell (behind origin/main)."
    echo "[INFO] Bitte zuerst ausführen: git pull"
    exit 1
  elif [[ "$REMOTE_HASH" == "$BASE_HASH" ]]; then
    echo "[WARNING] Lokaler Branch ist vor origin/main (ahead)."
    echo "[INFO] Empfohlen: Änderungen pushen bevor Release gebaut wird."
  else
    echo "[ERROR] Lokaler und Remote-Branch sind divergent."
    echo "[INFO] Bitte manuell lösen (merge/rebase)."
    exit 1
  fi
fi

# 4) Jetzt sicher pull durchführen
echo "[INFO] Repository ist sauber und aktuell → git pull"
git pull

echo "[INFO] Alten Build entfernen"
rm -rf build dist

echo "[INFO] Neue macOS App erstellen"
pyinstaller \
  --windowed \
  --name BooktrackQR \
  --paths src \
  --add-data "pic:pic" \
  src/main.py

if [[ ! -d "${APP_PATH}" ]]; then
  echo "[ERROR] App nicht gefunden: ${APP_PATH}"
  exit 1
fi

# Kamera-Berechtigung in Info.plist hinzufügen (macOS Pflicht)
APP_PLIST="dist/BooktrackQR.app/Contents/Info.plist"

if [[ -f "$APP_PLIST" ]]; then
  echo "[INFO] Setze macOS Kamera-Berechtigung"

  /usr/libexec/PlistBuddy -c "Add :NSCameraUsageDescription string 'Diese App benötigt Zugriff auf die Kamera zum Scannen von QR-Codes in der Schulbibliothek.'" "$APP_PLIST" 2>/dev/null || echo "[INFO] Kamera-Berechtigung existiert bereits"

else
  echo "[ERROR] Info.plist nicht gefunden – Kamera-Fix fehlgeschlagen"
  exit 1
fi

echo "[INFO] DMG erstellen"
./scripts/create_dmg.sh

if [[ ! -f "${DMG_PATH}" ]]; then
  echo "[ERROR] DMG nicht gefunden: ${DMG_PATH}"
  exit 1
fi

echo "[INFO] DMG umbenennen: ${DMG_RENAMED_PATH}"
mv "${DMG_PATH}" "${DMG_RENAMED_PATH}"

# README Version automatisch aktualisieren
README_PATH="${PROJECT_DIR}/README.md"

if [[ -f "${README_PATH}" ]]; then
  echo "[INFO] Aktualisiere README Version → V1.${VERSION}"
  # macOS kompatibles sed (BSD)
  sed -i '' -E "s/^Version: .*/Version: V1.${VERSION}/" "${README_PATH}"
else
  echo "[WARNING] README.md nicht gefunden – Version konnte nicht aktualisiert werden"
fi

echo "[INFO] Release abgeschlossen"
echo "[INFO] Ergebnis: ${DMG_RENAMED_PATH}"
