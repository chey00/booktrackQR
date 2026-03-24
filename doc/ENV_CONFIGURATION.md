# 24.03.26// Denis 
 # BooktrackQR – ENV Configuration (.env)

  ## Zweck

  Die .env Datei enthält alle vertraulichen Konfigurationsdaten der Anwendung, insbesondere die Verbindung zur Datenbank.

  👉 Ohne gültige .env Datei kann die App nicht gestartet werden.

  ———

  ## Speicherort (WICHTIG)

  Die .env Datei muss sich immer außerhalb des Projekts befinden:

    ~/Library/Application Support/BooktrackQR/.env

  Regeln:

  - ❌ Nicht im GitHub Repository speichern
  - ❌ Nicht im .app / .dmg Bundle enthalten
  - ✅ Immer lokal auf dem Gerät erstellen

  Grund: Sicherheit (keine Zugangsdaten im Code oder Bundle)

  ———

  ## Aufbau der .env Datei

    DB_HOST=192.168.xx.xxx
    DB_PORT=xxxx
    DB_NAME=xxxxxx
    DB_USER=xxxxxx
    DB_PASSWORD=DEIN_PASSWORT
    DB_CONNECT_TIMEOUT=20

  ———

  ## Bedeutung der Variablen

  | Variable | Beschreibung |
  | --- | --- |
  | DB_HOST | IP-Adresse des Datenbankservers (Raspberry Pi) |
  | DB_PORT | Port der Datenbank (Standard: 3306) |
  | DB_NAME | Name der Datenbank |
  | DB_USER | Datenbank-Benutzer |
  | DB_PASSWORD | Passwort des Benutzers |
  | DB_CONNECT_TIMEOUT | Timeout für Verbindungsversuche (Sekunden) |

  ———

  ## Wichtige Regeln

  - Keine Leerzeichen um =

  ❌ DB_HOST = 192.168.1.1
  ✅ DB_HOST=192.168.1.1

  - Keine Anführungszeichen verwenden
  - Jede Variable in eine neue Zeile
  - Groß-/Kleinschreibung beachten

  ———

  ## Typische Fehler & Lösungen

  ### ❌ App startet nicht

  Ursache:

  - .env fehlt oder liegt am falschen Ort

  Lösung:

  - Prüfen, ob Datei existiert:

    ~/Library/Application Support/BooktrackQR/.env

  ———

  ### ❌ Datenbankverbindung schlägt fehl

  Ursache:

  - falsche Zugangsdaten

  Lösung:

  - .env prüfen:
  - IP-Adresse korrekt?
  - Benutzername korrekt?
  - Passwort korrekt?

  ———

  ### ❌ Verbindung funktioniert im Team nicht

  Ursache:

  - falsches Netzwerk

  Lösung:

  - Prüfen, ob Gerät im selben Netzwerk ist wie der Raspberry Pi

  ———

  ## Entwicklungsmodus (nur für Entwickler)

  Im lokalen Entwicklungsmodus kann alternativ eine .env im Projekt verwendet werden:

  src/.env

  WICHTIG:

  - Nur für lokale Tests
  - Wird im Build nicht verwendet
  - Nicht ins Repository committen

  ———

  ## Zusammenfassung

  - .env ist zwingend erforderlich
  - .env liegt immer im User-Ordner
  - .env wird nie mit ausgeliefert
  - Fehler in der .env sind die häufigste Ursache für Probleme
