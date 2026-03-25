# Das ist der Code um QR Codes zu enerieren.
#  Dieser Code muss noch in das spätere Bücher App Projekt eingefügt werden.
############################################################################################
# 10.02.26 // Denis; Luis
# Abgeänert am 11.02.26 // Denis
#############################################################################################
# - QR-Code wird nur aus der Buch-ID generiert,
# damit die QR-Codes nicht zu komplex werden
# und auch von älteren Handys gescannt werden können.


from qr_generation.workflow import create_qr


def generate_qr_for_isbn(isbn_raw: str, counter: int | None = None, test_mode: bool = False):
    """
    High-level API: erzeugt QR-Payload und Bild im Speicher.
    - Produktiv: keine Dateispeicherung
    - Testmodus: optionale PNG-Speicherung im User-Data-Ordner
    """
    meta, image, file_path = create_qr(isbn_raw, counter, test_mode=test_mode)
    if test_mode and file_path:
        meta["qr_path"] = file_path
        meta["qr_image"] = image
    return meta

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
