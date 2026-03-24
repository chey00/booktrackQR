# 24.03.26// Denis 
————————————————————————————————————————————————————————————————————————
# BooktrackQR – Installation auf macOS (Team-Anleitung)

  ## Zweck dieser Anleitung

  Diese Anleitung zeigt Schritt für Schritt, wie die BooktrackQR-App auf einem Mac installiert und gestartet wird.

  👉 Ziel:
  Jedes Teammitglied soll die App ohne technische Vorkenntnisse starten können.

  ———

  ## Voraussetzungen

  - macOS (MacBook / iMac)
  - Zugriff auf die bereitgestellte .dmg Datei
  - Zugangsdaten zur Datenbank (für .env Datei)

  ———

  ## Installation der App (.dmg)

  1. .dmg Datei doppelt klicken
  2. Es öffnet sich ein Fenster mit der App
  3. Ziehe BooktrackQR.app in den Ordner „Programme“

  👉 Wichtig:
  Die App nicht direkt aus dem DMG starten, sondern immer aus „Programme“.

  ———

  ## Wichtiger Schritt: .env Datei erstellen

  Die App benötigt eine Konfigurationsdatei mit den Datenbank-Zugangsdaten.

  ### 1. Ordner erstellen

  Öffne das Terminal und führe aus:

  mkdir -p ~/Library/Application\ Support/BooktrackQR

  ### 2. .env Datei erstellen

  nano ~/Library/Application\ Support/BooktrackQR/.env

  ### 3. Inhalt einfügen

  .env-Datei Inhalt:

  DB_HOST=192.168.xx.xxx
  DB_PORT=xxxx
  DB_NAME=xxxxxxxx
  DB_USER=xxxxxxxx
  DB_PASSWORD=DEIN_PASSWORT
  DB_CONNECT_TIMEOUT=20

  👉 Wichtig:

  - Keine Leerzeichen vor oder nach =
  - Werte exakt eintragen
  - Passwort korrekt setzen

  ### 4. Datei speichern

  CTRL + O → Enter

  CTRL + X

  ———

  ## App starten

  1. Öffne Programme
  2. Starte BooktrackQR.app

  ———

  ## Erster Start unter macOS (Sicherheitswarnung)

  Da die App nicht signiert ist, zeigt macOS eine Warnung.

  Lösung:

  1. Rechtsklick auf BooktrackQR.app
  2. „Öffnen“ auswählen
  3. Bestätigen

  ———

  ## Typische Probleme & Lösungen

  ### ❌ App startet nicht

  ➡️ Ursache: .env fehlt oder falsch

  ✔️ Lösung:

  - Prüfen, ob Datei hier liegt:

  ~/Library/Application Support/BooktrackQR/.env

  ———

  ### ❌ Datenbankverbindung schlägt fehl

  ➡️ Ursache: falsche Zugangsdaten

  ✔️ Lösung:

  - .env prüfen (IP, Benutzer, Passwort)

  ———

  ### ❌ Leeres Fenster / keine Inhalte

  ➡️ Ursache: Verbindung zur Datenbank fehlt

  ✔️ Lösung:

  - .env prüfen
  - Netzwerkverbindung prüfen

  ———

  ### ❌ Sicherheitswarnung blockiert Start

  ✔️ Lösung:

  - Rechtsklick → Öffnen (siehe oben)

  ———

  ## Wichtige Hinweise

  - Die .env Datei ist nicht im Projekt enthalten
  - Die .env Datei wird nicht automatisch erstellt
  - Ohne .env funktioniert die App nicht

  👉 Das ist eine bewusste Sicherheitsentscheidung

  ———

  ## Support

  Bei Problemen bitte melden mit:

  - Screenshot der Fehlermeldung
  - Info, bei welchem Schritt das Problem auftritt
