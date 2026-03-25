# QR-Code-Logik – Technische Dokumentation

## 1. Ziel der QR-Code-Logik

Die QR-Codes dienen der eindeutigen Identifikation von Buchexemplaren im Ausleihprozess.
Im realen Ablauf wird ein QR-Code erzeugt, gedruckt, auf ein Buch geklebt und danach nicht mehr
als Bilddatei benötigt. Deshalb werden QR-Bilder im Produktivbetrieb **nicht dauerhaft gespeichert**,
sondern nur im Speicher erzeugt und unmittelbar weiterverwendet (z. B. für den Druck).

Realer Ablauf:
1. QR erzeugen
2. drucken
3. auf Buch kleben
4. fertig

## 2. Überblick der neuen Architektur

Neuer Ordner: `src/qr_generation/`

Dateien:
- `payload.py`  
  Erzeugt und validiert den QR-Inhalt (Payload), inklusive ISBN-Normalisierung.
- `image.py`  
  Erzeugt das QR-Bild im Speicher aus der Payload, ohne Dateischreibung.
- `workflow.py`  
  Orchestriert den End-to-End-Ablauf: Counter, Payload, Bild, Logging, optionaler Test-Export.

## 3. Technischer Ablauf (End-to-End)

1. **ISBN wird übergeben** (z. B. vom GUI-Workflow).
2. **ISBN wird normalisiert** (`normalize_isbn`), nur ISBN-13 Ziffern.
3. **Counter wird ermittelt** (`get_next_counter_local`), pro ISBN persistent.
4. **Payload wird erzeugt** (`generate_qr_payload`).
5. **QR-Bild wird im Speicher erzeugt** (`generate_qr_image`).
6. **Metadaten werden geloggt** (`log_qr_creation`).
7. **Optional (Testmodus)**: PNG wird gespeichert.

## 4. QR-Payload-Format

Format:
```
BOOK|ISBN13|COUNTER
```

Bedeutung:
- `BOOK` = fixer Präfix zur Typkennzeichnung
- `ISBN13` = normalisierte ISBN-13, nur Ziffern
- `COUNTER` = laufende Nummer pro ISBN (5-stellig)

Das Format ist bewusst kurz und robust, damit der QR-Code gut scanbar bleibt.

## 5. Counter-Logik

Der Counter wird pro ISBN in einer JSON-Datei gespeichert:
```
~/Library/Application Support/BooktrackQR/QR/counters.json
```

Technik:
- Laden der JSON-Daten beim Erzeugen
- Inkrement pro ISBN
- Atomisches Schreiben (Temp-Datei + `os.replace`)

Dadurch werden doppelte QR-Codes verhindert.

## 6. Logging-Konzept

Geloggte Daten:
- `isbn13`
- `counter`
- `payload`
- `created_at`
- `status`

Speicherort:
```
~/Library/Application Support/BooktrackQR/QR/qr_log.jsonl
```

Es werden **keine Bilddaten** gespeichert, nur fachlich relevante Metadaten.

## 7. Unterschied: Produktivmodus vs Testmodus

Produktivmodus:
- keine Speicherung von PNG-Dateien
- QR-Bild existiert nur im Speicher

Testmodus:
- optionale Speicherung von PNG-Dateien
- Speicherung im User-Data-Ordner:
  `~/Library/Application Support/BooktrackQR/QR/images`

## 8. Änderungen zur alten Implementierung

Alt:
- `QR_Generator.py` enthielt alles (Payload, Bild, Speicherung, Counter)
- PNG-Dateien wurden erzeugt und gespeichert
- keine klare Trennung der Verantwortlichkeiten

Neu:
- klare Trennung (Payload / Image / Workflow)
- keine Speicherung im Produktivmodus
- bessere Wartbarkeit und klare Schnittstellen

## 9. Offene Punkte / zukünftige Erweiterungen

- **Druckfunktion** (`print_qr_image`) ist aktuell nur ein Stub.
  Die vollständige Druckimplementierung ist **nicht Bestandteil dieses PBIs**
  und wird im dafür vorgesehenen separaten PBI umgesetzt.
- Mögliche nächste Schritte:
  - echte Druckschnittstelle
  - DB-Logging statt JSONL
  - GUI-Integration prüfen und verfeinern
