import json
import os
import tempfile
from datetime import datetime

from app_paths import ensure_user_data_dir, user_data_path
from .payload import normalize_isbn, generate_qr_payload
from .image import generate_qr_image


def _counter_store_path() -> str:
    return user_data_path("QR", "counters.json")


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


def get_next_counter_local(isbn13: str) -> int:
    """
    Counter pro ISBN, gespeichert im User-Data-Ordner (keine Indexdatei).
    """
    counter_path = _counter_store_path()
    counters = _load_counters(counter_path)
    current = int(counters.get(isbn13, 0))
    next_counter = current + 1
    counters[isbn13] = next_counter
    _atomic_write_json(counter_path, counters)
    return next_counter


def log_qr_creation(meta: dict) -> None:
    """
    Protokolliert fachlich relevante Metadaten (kein Bild).
    """
    ensure_user_data_dir()
    log_path = user_data_path("QR", "qr_log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")


def print_qr_image(image, meta: dict) -> dict:
    """
    Platzhalter für spätere Drucklogik.

    WICHTIG:
    - Die vollständige Druckimplementierung ist NICHT Bestandteil dieses PBIs.
    - Die echte Umsetzung erfolgt in einem separaten, dafür vorgesehenen PBI.
    - Diese Stub-Lösung darf den restlichen Ablauf nicht blockieren.

    Verhalten:
    - Führt keinen echten Druck aus.
    - Gibt ein neutrales Statusobjekt zurück.
    - Wirft keine Exceptions, um App-Start und QR-Workflow nicht zu stören.
    """
    try:
        _ = (image, meta)  # bewusst ungenutzt
        return {
            "status": "not_implemented",
            "message": "Druckfunktion ist eine Stub-Vorlage und wird im separaten PBI umgesetzt.",
        }
    except Exception:
        # Schutz vor unerwarteten Fehlern: niemals den Workflow blockieren
        return {
            "status": "not_implemented",
            "message": "Druckfunktion ist nicht aktiv (Stub).",
        }


def create_qr(isbn_raw: str, counter: int | None = None, test_mode: bool = False):
    """
    End-to-end Workflow:
    - Payload erzeugen
    - Bild im Speicher erzeugen
    - Metadaten loggen
    - optional: Bild im Testmodus speichern
    """
    isbn13 = normalize_isbn(isbn_raw)
    if counter is None:
        counter = get_next_counter_local(isbn13)

    payload = generate_qr_payload(isbn13, counter)
    image = generate_qr_image(payload)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta = {
        "isbn13": isbn13,
        "counter": counter,
        "payload": payload,
        "created_at": timestamp,
        "status": "CREATED",
    }

    log_qr_creation(meta)

    file_path = None
    if test_mode:
        qr_root_dir = ensure_user_data_dir("QR")
        qr_images_dir = os.path.join(qr_root_dir, "images")
        os.makedirs(qr_images_dir, exist_ok=True)

        base_filename = f"QR_BOOK_{isbn13}_{counter:05d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = os.path.join(qr_images_dir, base_filename + ".png")
        counter_file = 1
        while os.path.exists(file_path):
            file_path = os.path.join(qr_images_dir, f"{base_filename}_{counter_file}.png")
            counter_file += 1

        image.save(file_path)
        meta["qr_path"] = file_path

    return meta, image, file_path
