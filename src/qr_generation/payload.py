import re


def normalize_isbn(isbn_raw: str) -> str:
    """
    Normalize scanner output to ISBN-13 digits-only.
    """
    digits = re.sub(r"[^0-9]", "", str(isbn_raw))
    if len(digits) != 13:
        raise ValueError(f"Ungültige ISBN-13 (erwartet 13 Ziffern): {isbn_raw}")
    return digits


def generate_qr_payload(isbn13: str, counter: int) -> str:
    """
    Variante A: QR-Payload nur aus ISBN + Counter.
    Format: BOOK|ISBN13|COUNTER(5-stellig)
    """
    if counter < 1:
        raise ValueError("Counter muss >= 1 sein")
    return f"BOOK|{isbn13}|{counter:05d}"
