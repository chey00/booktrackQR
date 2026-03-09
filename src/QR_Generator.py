# Das ist der Code um QR Codes zu enerieren.
#  Dieser Code muss noch in das spätere Bücher App Projekt eingefügt werden.
############################################################################################
# 10.02.26 // Denis; Luis
# Abgeänert am 11.02.26 // Denis
#############################################################################################
# - QR-Code wird nur aus der Buch-ID generiert,
# damit die QR-Codes nicht zu komplex werden
# und auch von älteren Handys gescannt werden können.


import qrcode
import os
import re
import json
import tempfile
import hashlib
import logging
from datetime import datetime


def normalize_isbn(isbn_raw: str) -> str:
    """Normalize scanner output to ISBN-13 digits-only.

    Accepts inputs like "978-3-589-24132-3" and returns "9783589241323".
    """
    digits = re.sub(r"[^0-9]", "", str(isbn_raw))
    if len(digits) != 13:
        raise ValueError(f"Ungültige ISBN-13 (erwartet 13 Ziffern): {isbn_raw}")
    return digits


def build_payload(isbn13: str, counter: int) -> str:
    """Builds the QR payload (Variante B): BOOK|ISBN13|COUNTER(5-stellig)."""
    if counter < 1:
        raise ValueError("Counter muss >= 1 sein")
    return f"BOOK|{isbn13}|{counter:05d}"


def _counter_index_paths(base_dir: str) -> tuple[str, str]:
    """Returns (index_dir, counter_file_path)."""
    index_dir = os.path.join(base_dir, "QR", "index")
    counter_file = os.path.join(index_dir, "isbn_counter.json")
    return index_dir, counter_file


def _load_counters(counter_file: str) -> dict:
    if not os.path.exists(counter_file):
        return {}
    try:
        with open(counter_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Falls Datei korrupt/leer ist: nicht crashen, sondern neu starten
        return {}


def _atomic_write_json(path: str, data: dict) -> None:
    """Write JSON atomically (temp file + replace)."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def _compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file (used for integrity / later DB checks)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_next_counter_local(isbn13: str, base_dir: str) -> int:
    """Local counter per ISBN (Übergangslösung ohne DB).

    Stores the next counter in: src/QR/index/isbn_counter.json
    """
    index_dir, counter_file = _counter_index_paths(base_dir)
    os.makedirs(index_dir, exist_ok=True)

    counters = _load_counters(counter_file)
    current = int(counters.get(isbn13, 0))
    next_counter = current + 1
    counters[isbn13] = next_counter
    _atomic_write_json(counter_file, counters)
    return next_counter


def _qr_index_file_path(base_dir: str) -> str:
    return os.path.join(base_dir, "QR", "index", "qr_codes_index.json")


def _load_qr_index(index_path: str) -> list:
    if not os.path.exists(index_path):
        return []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _append_to_qr_index(base_dir: str, meta: dict) -> None:
    index_path = _qr_index_file_path(base_dir)
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    index_data = _load_qr_index(index_path)

    # Duplikatprüfung über payload
    for entry in index_data:
        if entry.get("payload") == meta.get("payload"):
            return  # bereits vorhanden → nicht erneut speichern

    index_data.append(meta)
    _atomic_write_json(index_path, index_data)


# NEW: QR-Code history listing function
def list_qr_codes(isbn13: str | None = None, limit: int | None = None, newest_first: bool = True) -> list[dict]:
    """Returns QR generation history from src/QR/index/qr_codes_index.json.

    - isbn13: optional filter
    - limit: optional max number of entries
    - newest_first: sort by created_at descending (default)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = _qr_index_file_path(base_dir)
    data = _load_qr_index(index_path)

    if isbn13 is not None:
        data = [e for e in data if str(e.get("isbn13")) == str(isbn13)]

    # Sort by created_at (string 'YYYY-MM-DD HH:MM:SS' sorts lexicographically)
    data.sort(key=lambda e: str(e.get("created_at", "")), reverse=newest_first)

    if limit is not None:
        data = data[: int(limit)]

    return data


def generate_qr_for_isbn(isbn_raw: str):
    """High-level API: normalizes ISBN, gets next local counter,
    generates QR + log and writes meta entry into qr_codes_index.json

    Returns: meta-dict
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    isbn13 = normalize_isbn(isbn_raw)
    counter = get_next_counter_local(isbn13, base_dir)
    file_path, log_path, qr_sha256 = save_qr_image(isbn13, counter)
    payload = build_payload(isbn13, counter)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    meta = {
        "isbn13": isbn13,
        "counter": counter,
        "payload": payload,
        "qr_path": file_path,
        "log_path": log_path,
        "qr_sha256": qr_sha256,
        "created_at": timestamp,
        "status": "CREATED"
    }

    _append_to_qr_index(base_dir, meta)

    return meta


def save_qr_image(isbn_raw: str, counter: int):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Neues Verzeichnis: src/QR/
    qr_root_dir = os.path.join(base_dir, "QR")

    # Unterordner entsprechend Funktion
    qr_images_dir = os.path.join(qr_root_dir, "images")
    qr_logs_dir = os.path.join(qr_root_dir, "logs")

    os.makedirs(qr_images_dir, exist_ok=True)
    os.makedirs(qr_logs_dir, exist_ok=True)

    # Index-Verzeichnis (für lokale Counter-Übergangslösung)
    qr_index_dir = os.path.join(qr_root_dir, "index")
    os.makedirs(qr_index_dir, exist_ok=True)

    # ISBN normalisieren + Payload bauen (Variante B)
    isbn13 = normalize_isbn(isbn_raw)
    payload = build_payload(isbn13, counter)

    # QR-Code aus Payload erzeugen
    qr = qrcode.QRCode(version=1, box_size=40, border=3)
    qr.add_data(payload)
    qr.make(fit=True)

    image = qr.make_image(fill_color='black', back_color='white')

    # Timestamp erzeugen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_filename = f"QR_BOOK_{isbn13}_{counter:05d}_{timestamp}"
    file_path = os.path.join(qr_images_dir, base_filename + ".png")

    counter_file = 1
    while os.path.exists(file_path):
        file_path = os.path.join(
            qr_images_dir,
            f"{base_filename}_{counter_file}.png"
        )
        counter_file += 1

    image.save(file_path)

    # Einzelne Bestandteile
    dateiname = os.path.basename(file_path)
    dateipfad = os.path.dirname(file_path)
    formatted_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Passende Logdatei zum QR-Code (pro QR-Code eine eigene .log Datei)
    log_filename = f"{base_filename}.log"
    log_path = os.path.join(qr_logs_dir, log_filename)

    logger = logging.getLogger(f"qr_{base_filename}")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # verhindert Doppel-Logs über Root-Logger

    # Handler nur für dieses Logfile
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Hash berechnen (für Log-Integrität)
    qr_sha256 = _compute_sha256(file_path)

    logger.info(
        "QR-CODE ERSTELLT\n"
        f"Datum: {formatted_date}\n"
        f"ISBN13: {isbn13}\n"
        f"Counter: {counter:05d}\n"
        f"Payload: {payload}\n"
        f"QR-Datei: {file_path}\n"
        f"Log-Datei: {log_path}\n"
        f"SHA256: {qr_sha256}"
    )

    # Handler wieder entfernen, damit bei erneutem Aufruf nichts doppelt geloggt wird
    logger.removeHandler(file_handler)
    file_handler.close()

    # Bestätigung in der Konsole
    print(
        f"Erstellt: {dateiname} + {log_filename} | "
        f"QR-Pfad: {dateipfad} | Log-Pfad: {qr_logs_dir} | "
        f"ISBN13: {isbn13} | Counter: {counter:05d} | Payload: {payload} | Datum: {formatted_date}"
    )
    return file_path, log_path, qr_sha256

#########################################################################################################
# AB Hier kannst du den Code testen, indem du dieses Skript direkt ausführst.
# Es erzeugt dann einen QR-Code und ein Logfile im entsprechenden Ordner.
######################################################################################################

if __name__ == "__main__":
    # Mini-Testlauf: erzeugt 1 QR + 1 Log im Ordner src/QR/images und src/QR/logs
    # Beispiel aus deinem Foto: 978-3-589-24132-3
    try:
        test_isbn_raw = "978-3-589-24132-3"
        meta = generate_qr_for_isbn(test_isbn_raw)
        print("✅ Test erfolgreich")
        print("\n--- META OUTPUT ---")
        print(json.dumps(meta, indent=2, ensure_ascii=False))
        print("\n--- HISTORY (letzte 5) ---")
        history = list_qr_codes(limit=5)
        print(json.dumps(history, indent=2, ensure_ascii=False))
    except Exception as e:
        print("❌ Test fehlgeschlagen")
        raise
