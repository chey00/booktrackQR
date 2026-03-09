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


def _counter_store_path(base_dir: str) -> str:
    return os.path.join(base_dir, "QR", "counters.json")


def _load_counters(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _atomic_write_json(path: str, data: dict) -> None:
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


def get_next_counter_local(isbn13: str, base_dir: str) -> int:
    """Counter pro ISBN, gespeichert in src/QR/counters.json (keine Indexdatei)."""
    counter_path = _counter_store_path(base_dir)
    counters = _load_counters(counter_path)
    current = int(counters.get(isbn13, 0))
    next_counter = current + 1
    counters[isbn13] = next_counter
    _atomic_write_json(counter_path, counters)
    return next_counter


def generate_qr_for_isbn(isbn_raw: str, counter: int | None = None, test_mode: bool = False):
    """High-level API: normalizes ISBN, uses provided counter, generates QR.

    - test_mode=True: speichert PNG, gibt Pfad + Payload aus
    - test_mode=False: keine Ausgabe, keine Speicherung
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    isbn13 = normalize_isbn(isbn_raw)
    if counter is None:
        counter = get_next_counter_local(isbn13, base_dir)
    file_path, payload, qr_image = save_qr_image(isbn13, counter, test_mode=test_mode)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    meta = {
        "isbn13": isbn13,
        "counter": counter,
        "payload": payload,
        "created_at": timestamp,
        "status": "CREATED",
        "qr_image": qr_image,
    }

    if test_mode:
        meta["qr_path"] = file_path

    return meta


def save_qr_image(isbn_raw: str, counter: int, test_mode: bool = False):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Speicherort nur im Testmodus
    qr_images_dir = None
    if test_mode:
        qr_root_dir = os.path.join(base_dir, "QR")
        qr_images_dir = os.path.join(qr_root_dir, "images")
        os.makedirs(qr_images_dir, exist_ok=True)

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
    file_path = None
    if test_mode:
        file_path = os.path.join(qr_images_dir, base_filename + ".png")

        counter_file = 1
        while os.path.exists(file_path):
            file_path = os.path.join(
                qr_images_dir,
                f"{base_filename}_{counter_file}.png"
            )
            counter_file += 1

    if test_mode:
        image.save(file_path)

        # Bestätigung in der Konsole (nur Testmodus)
        dateiname = os.path.basename(file_path)
        dateipfad = os.path.dirname(file_path)
        formatted_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(
            f"Erstellt: {dateiname} | "
            f"QR-Pfad: {dateipfad} | "
            f"ISBN13: {isbn13} | Counter: {counter:05d} | Payload: {payload} | Datum: {formatted_date}"
        )

    return file_path, payload, image

#########################################################################################################
# AB Hier kannst du den Code testen, indem du dieses Skript direkt ausführst.
# Es erzeugt dann einen QR-Code und ein Logfile im entsprechenden Ordner.
######################################################################################################

if __name__ == "__main__":
    # Mini-Testlauf: erzeugt 1 QR im Ordner src/QR/images
    # Beispiel aus deinem Foto: 978-3-589-24132-3
    try:
        test_isbn_raw = "978-3-589-24132-3"
        test_counter = 1
        meta = generate_qr_for_isbn(test_isbn_raw, test_counter, test_mode=True)
        print("✅ Test erfolgreich")
        print("\n--- META OUTPUT ---")
        print(meta)
    except Exception as e:
        print("❌ Test fehlgeschlagen")
        raise
