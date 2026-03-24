# 24.03.26// Denis
 # BooktrackQR – DMG Release Workflow

  ## Ziel

  Wiederholbarer, schneller und fehlerfreier DMG-Release-Prozess für interne Test-Releases.

  ———

  ## Voraussetzungen

  - Projekt ist aktuell (git pull)
  - Virtuelle Umgebung ist aktiv (.venv)
  - .env ist korrekt eingerichtet (für Tests)
  - PyInstaller ist installiert

  ———

  ## Workflow

  ### 1. Projekt vorbereiten

    cd <lokaler-repo-ordner>
    source .venv/bin/activate
    git pull

  ### 2. Alten Build entfernen

    rm -rf build dist

  ### 3. Neue .app erstellen

    pyinstaller \
      --windowed \
      --name BooktrackQR \
      --paths src \
      --add-data "pic:pic" \
      src/main.py

  Ergebnis: 
  
    dist/BooktrackQR.app

  ### 4. .dmg erstellen

    ./scripts/create_dmg.sh

  Ergebnis: 
  
    dist/BooktrackQR.dmg

  ### 5. Tests durchführen

  #### 5.1 Direkt testen

    open dist/BooktrackQR.app

  Prüfen:

  - Startet die App?
  - GUI sichtbar?
  - Keine Fehlermeldung?

  #### 5.2 Installation simulieren

    mkdir -p test_install
    cp dist/BooktrackQR.dmg test_install/
    cd test_install
    open BooktrackQR.dmg

  Manuell:

  - App nach „Programme“ ziehen
  - App starten

  #### 5.3 Funktionstest

  Prüfen:

  - .env wird erkannt
  - DB-Verbindung funktioniert
  - GUI lädt korrekt

  ———

  ## Checkliste vor Veröffentlichung

  - [ ] App startet ohne Fehler
  - [ ] GUI funktioniert
  - [ ] .env wird korrekt geladen
  - [ ] Datenbankverbindung funktioniert
  - [ ] DMG öffnet sich korrekt
  - [ ] Installation per Drag & Drop funktioniert

  ———

  ## Versionierung

  Versionsnummer im Dateinamen: V1.<Sprintnummer>

  Beispiele:

  - BooktrackQR_V1.1.dmg
  - BooktrackQR_V1.2.dmg

  Aktuell (Sprint 6):

  - BooktrackQR_V1.6.dmg

  ———

  ## Verteilung

  - .dmg an Teammitglieder weitergeben
  - Optional: Upload in GitHub (Release oder separater Branch)

  ———

  ## Wichtige Hinweise

  - .env ist nicht im DMG enthalten
  - Nutzer müssen .env selbst erstellen:

  ~/Library/Application Support/BooktrackQR/.env

  - Ohne .env startet die App nicht

  ———

  ## Abgrenzung

  Diese Anleitung ist:

  - ❌ Keine finale Release-Pipeline
  - ❌ Kein App Store Workflow
  - ❌ Keine Signierung / Notarization

  Nur für interne Test-Releases

  ———

  ## Zielbild

  Mit diesem Workflow soll jede neue Version:

  - schnell erstellt werden
  - reproduzierbar sein
  - zuverlässig getestet werden
