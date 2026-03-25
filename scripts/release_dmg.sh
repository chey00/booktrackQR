#!/usr/bin/env bash
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

echo "[INFO] Repository aktualisieren"
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

echo "[INFO] DMG erstellen"
./scripts/create_dmg.sh

if [[ ! -f "${DMG_PATH}" ]]; then
  echo "[ERROR] DMG nicht gefunden: ${DMG_PATH}"
  exit 1
fi

echo "[INFO] DMG umbenennen: ${DMG_RENAMED_PATH}"
mv "${DMG_PATH}" "${DMG_RENAMED_PATH}"

echo "[INFO] Release abgeschlossen"
echo "[INFO] Ergebnis: ${DMG_RENAMED_PATH}"
