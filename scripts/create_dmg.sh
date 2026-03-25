#!/usr/bin/env bash
set -euo pipefail

# Minimaler DMG-Build für interne Tests.
# WICHTIG: Kein Signing, keine Notarization.
# Erwartet: dist/BooktrackQR.app

APP_NAME="BooktrackQR"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${APP_NAME}.dmg"
STAGING_DIR="dist/_dmg_staging"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Fehler: ${APP_PATH} nicht gefunden. Bitte zuerst den .app Build erstellen."
  exit 1
fi

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"

# Optional: Applications-Link für Drag&Drop
ln -sf /Applications "$STAGING_DIR/Applications"

rm -f "$DMG_PATH"
hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "DMG erstellt: ${DMG_PATH}"
