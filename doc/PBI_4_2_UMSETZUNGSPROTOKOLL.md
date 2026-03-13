10.03.26 // Denis

13.03.26 // letzte änderungen; Fertigstellung des Protokolls
# PBI 4.2 – Umsetzungprotokoll (Zwischenstand)

## 1. Projektkontext
- Projektname: **BooktrackQR**
- Technologie: **Python**, **PyQt6**, **MySQL/MariaDB**
- Ziel: Bibliotheks- und Buchverwaltung mit QR-Code-System
- Rolle der PBI 4.2: Einführung von **schreibendem Zugriff** (Daten anlegen, bearbeiten, löschen) in den Verwaltungs-Views und Umstellung von Dummy-Daten auf echte DB-Operationen.

## 2. Ausgangszustand vor der Umsetzung
Der Zustand vor der PBI‑4.2‑Umsetzung (Soll-/Zielabgrenzung für diese Arbeiten):
- Buchverwaltung und Schülerverwaltung arbeiteten mit Dummy-Daten.
- keine echte Datenbankanbindung in den GUI-Views.
- DB-Verbindung wurde nur im `LoadingGate` getestet.
- CRUD-Funktionen existierten nur als lokale Listenoperationen.
- keine echten Insert/Update/Delete Operationen auf der Datenbank.

## 3. Architekturänderungen

### Neue Datei
- `src/db_access.py`
  - zentrale DB-Zugriffsschicht (pymysql)
  - kapselt SQL-Zugriffe
  - Funktionen:
    - `get_connection(cfg)`
    - `fetch_all(cfg, sql, params)`
    - `fetch_one(cfg, sql, params)`
    - `execute(cfg, sql, params)`
  - `autocommit=False` mit explizitem `commit()/rollback()` in `execute()`

### Änderungen an Konfiguration und App-Start
- `src/loading_gate.py`
  - DB-Konfiguration wird aus `.env` geladen (`load_db_config`) über `python-dotenv`
  - geprüfte ENV-Keys: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CONNECT_TIMEOUT`
  - DB-Verbindung wird geprüft (`check_db_connection`) und anschließend `cfg` gespeichert
  - `cfg` wird nach erfolgreicher Prüfung an die App übergeben (`on_success(self.cfg)`)

- `src/main.py`
  - `LoadingGate` übernimmt den Start und ruft `open_main(cfg)` auf
  - `open_main` instanziert `MainWindow(cfg)` und zeigt das Hauptfenster

- `src/MainWindow.py`
  - `cfg` wird in die Verwaltungswidgets injiziert:
    - `SchuelerverwaltungWidget(cfg)`
    - `BuchverwaltungWidget(cfg)`
  - andere Widgets bleiben unverändert (z. B. `RueckgabeWidget()` ohne DB-Kontext)

## 4. Umsetzung der CRUD-Funktionalität

### 4.1 Studierendenverwaltung
Datei: `src/Schuelerverwaltung.py`

Implementiert:
- Laden der Studierenden aus der DB (`load_students`) inkl. Join auf `Schulklasse` und `Schuljahr`
- Anlegen (`INSERT INTO Studierende`)
- Bearbeiten (`UPDATE Studierende`)
- Löschen (`DELETE FROM Studierende`)

Validierungen (Dialog `StudentDialog.validate_and_save()`):
- `studierende_id` Pflichtfeld
- `studierende_id` muss numerisch sein
- `vorname` Pflichtfeld
- `nachname` Pflichtfeld
- `status` nur `AKTIV` oder `INAKTIV`
- `schulklasse_id` muss ausgewählt sein

Löschregel:
- Löschung wird verhindert, wenn Einträge in `Ausleihe_Aktuell` existieren:
  - `SELECT 1 FROM Ausleihe_Aktuell WHERE studierende_id = %s LIMIT 1`

### 4.2 Buchverwaltung
Datei: `src/Buchverwaltung.py`

Implementiert:
- Laden der Buchtitel aus der DB (`load_books`)
- Anlegen (`INSERT INTO BuchTitel`)
- Bearbeiten (`UPDATE BuchTitel`)
- Löschen (`DELETE FROM BuchTitel`)

Validierungen (Dialog `BookDialog.validate_and_save()`):
- `titel_id` Pflichtfeld und numerisch
- `isbn` Pflichtfeld
- `titel` Pflichtfeld
- `verlag` Pflichtfeld
- `auflage` Pflichtfeld
- `auflage` muss > 0 sein

GUI-Verhalten:
- `titel_id` ist beim Bearbeiten **read-only**
- Bestand wird **read-only** in der Tabelle angezeigt (keine Bearbeitung der Exemplare über die GUI)
- Tabellenansicht wird nach jeder DB-Operation neu geladen

## 5. Anzeige des Bestands
Bestand wird dynamisch berechnet über:
- `COUNT(e.exemplar_id)`
- Join zwischen `BuchTitel` und `BuchExemplar`

SQL (aktueller Stand):
```
SELECT t.titel_id, t.isbn, t.titel, t.verlag, t.auflage,
       COUNT(e.exemplar_id) AS bestand
FROM BuchTitel t
LEFT JOIN BuchExemplar e ON e.isbn = t.isbn
GROUP BY t.titel_id, t.isbn, t.titel, t.verlag, t.auflage
ORDER BY t.titel_id;
```

## 6. Gefundenes Schema-Problem
Während der Tests wurde ein Datenbankschema-Mismatch entdeckt:
- ursprünglich angenommen: `BuchExemplar.titel_id → BuchTitel.titel_id`
- tatsächliche DB-Struktur: `BuchExemplar.isbn → BuchTitel.isbn`

Fehlerbild (bei falschem Join):
- `Unknown column 'e.titel_id' in 'ON'`

## 7. Korrektur des Datenbank-Joins
Die Abfrage in `load_books()` wurde korrigiert:

Falsch:
```
LEFT JOIN BuchExemplar e ON e.titel_id = t.titel_id
```

Richtig:
```
LEFT JOIN BuchExemplar e ON e.isbn = t.isbn
```

Ergebnis: Bestandsberechnung funktioniert wieder korrekt.

## 8. Anpassung der Löschlogik
Da die Verknüpfung über `isbn` erfolgt, wurde die Löschprüfung angepasst:

Neue Logik:
1. ISBN des Titels über `titel_id` ermitteln
2. prüfen, ob diese ISBN in `BuchExemplar` existiert
3. Löschen nur erlauben, wenn keine Exemplare existieren

SQL:
```
SELECT isbn FROM BuchTitel WHERE titel_id = %s
SELECT 1 FROM BuchExemplar WHERE isbn = %s LIMIT 1
```

## 9. Anpassungen an der GUI
- CRUD-Operationen greifen direkt auf die DB zu
- Dummy-Daten sind nicht mehr Teil der Verwaltungs-Views (Daten werden aus DB geladen)
- Tabellen werden nach jedem `INSERT/UPDATE/DELETE` neu geladen
- Bestand wird ausschließlich als read-only Spalte angezeigt

## 10. Aktueller Teststand
**Studierendenverwaltung:**
- ✔ Anlegen funktioniert (DB‑Insert)
- ✔ Bearbeiten funktioniert (DB‑Update)
- ✔ Löschen funktioniert (DB‑Delete)
- ✔ Validierungen greifen

**Buchverwaltung:**
- ✔ Anzeige der Buchtitel funktioniert
- ✔ Bestand wird berechnet (COUNT + Join)
- ✔ Insert / Update implementiert

Noch zu prüfen (mit DB‑Zugang):
- vollständiger Test der Buchverwaltung
- Verhalten bei vorhandenen `BuchExemplar`
- Löschprüfung mit echten Daten

## 11. Offene Punkte / nächste Schritte
- vollständiger Test der Buchverwaltung mit laufender DB
- mögliche Verbesserung der ISBN‑Duplikatsprüfung
- CSV‑Import‑Mapping robuster machen (Klassen-Labels vs. IDs)
- Logging-System statt `print()` für DB‑Fehler
- Refactoring: DB‑Zugriffe weiter zentralisieren und Fehlerbehandlung vereinheitlichen

---

**Zusammenfassung (aktueller Projektstand):**
BooktrackQR nutzt jetzt eine zentrale DB‑Zugriffsschicht und übergibt die DB‑Konfiguration vom `LoadingGate` bis in die Verwaltungswidgets. Die Studierenden- und Buchverwaltung führen echte CRUD‑Operationen gegen die MySQL/MariaDB‑Datenbank aus. Die Bestandsberechnung basiert auf einem korrekten `ISBN`‑Join zwischen `BuchTitel` und `BuchExemplar`. Offen sind vor allem vollständige Tests der Buchverwaltung und kleinere Qualitätsverbesserungen (z. B. ISBN‑Duplikate, Logging).

## 12. Code-Qualitätsprüfung und Endtest
Es wurde eine vollständige Analyse des Projekts durchgeführt. Geprüfte Module:
- `src/loading_gate.py`
- `src/main.py`
- `src/MainWindow.py`
- `src/db_access.py`
- `src/Schuelerverwaltung.py`
- `src/Buchverwaltung.py`

Kurzbefund:
- Architektur der DB-Anbindung: Konfiguration wird im `LoadingGate` aus `.env` geladen, geprüft und als `cfg` an `MainWindow` weitergereicht.
- Datenfluss ist korrekt: `LoadingGate` → `MainWindow` → Verwaltungswidgets (`SchuelerverwaltungWidget`, `BuchverwaltungWidget`).
- Verwendung von `db_access.py` ist konsistent für alle DB-Operationen (lesen und schreiben).
- Dummy-Daten wurden entfernt; alle Daten werden über SQL aus der Datenbank geladen.

## 13. Abgleich mit dem aktuellen Datenbankschema
Das Schema in `db/db_BooktrackQR.sql` wurde geprüft und als verbindliche Quelle verwendet.

Relevante Tabellen:
- `Schuljahr`
- `Schulklasse`
- `Studierende`
- `BuchTitel`
- `BuchExemplar`
- `Ausleihe_Aktuell`

Schema-Kernelemente:
- FK-Beziehungen zwischen `Schulklasse` → `Schuljahr`, `Studierende` → `Schulklasse`, `BuchExemplar` → `BuchTitel`, `Ausleihe_Aktuell` → `BuchExemplar` und `Studierende`.
- UNIQUE-Constraint auf `BuchTitel.isbn`.
- `ON UPDATE CASCADE` für alle relevanten FKs.
- `ON DELETE CASCADE` für alle relevanten FKs.

Ergebnis: Der aktuelle Code ist mit dem Schema kompatibel, inklusive der Join-Logik über ISBN und der Löschsperren.

## 14. Ergebnis des Endtests der PBI 4.2
**Studierendenverwaltung (src/Schuelerverwaltung.py):**
- Laden der Datensätze aus der DB
- Studierende anlegen (INSERT)
- Studierende bearbeiten (UPDATE)
- Studierende löschen (DELETE)
- Validierungen für Pflichtfelder, `studierende_id` numerisch, Status, Klasse
- Löschsperre bei aktiver Ausleihe in `Ausleihe_Aktuell`
- UI-Refresh nach Änderungen (Reload + Filter)

**Buchverwaltung (src/Buchverwaltung.py):**
- Laden der Buchtitel aus der DB
- Bestandsberechnung über Join zwischen `BuchTitel` und `BuchExemplar`
- Buchtitel anlegen (INSERT)
- Buchtitel bearbeiten (UPDATE)
- Buchtitel löschen (DELETE)
- Validierungen für Pflichtfelder, `titel_id` numerisch, `auflage > 0`
- Löschsperre bei vorhandenen Exemplaren in `BuchExemplar`
- UI-Refresh nach Änderungen (Reload + Filter)

## 15. Bekannte Einschränkungen
- ISBN kann aktuell im Bearbeitungsdialog geändert werden.
- ISBN-Duplikate werden aktuell nur durch die DB-Constraint abgefangen.

Begründung, warum kein Blocker: Die Datenintegrität ist durch die UNIQUE-Constraint und FK-Regeln geschützt; die PBI fordert schreibenden Zugriff (CRUD), der fachlich korrekt funktioniert. Die Einschränkungen betreffen nur Nutzerführung und sind als Qualitätsverbesserungen einzuordnen.

## 16. Abschlussbewertung der PBI 4.2
- CRUD-Operationen funktionieren vollständig.
- Die Anwendung arbeitet durchgängig mit der Datenbank.
- Validierungen greifen zuverlässig.
- Löschschutz ist implementiert und wirksam.
- Tabellen aktualisieren sich nach Änderungen korrekt.
- Keine Dummy-Daten mehr vorhanden.

Die PBI 4.2 kann im aktuellen Stand als abgeschlossen und abnahmefähig bewertet werden.
