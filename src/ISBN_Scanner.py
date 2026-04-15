# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: ISBN_Scanner (PBI 10.1.1 & Integration)
# Autoren: Mustafa Demiral, Ahmet Toplar
# Beschreibung: OpenCV Scanner für ISBN Barcodes mit Ziel-Overlay und Abbrechen-Button.
# ------------------------------------------------------------------------------
import cv2
from pyzbar.pyzbar import decode

# Globale Variable, um den Maus-Klick zu registrieren
abbruch_geklickt = False


def maus_klick_erkennen(event, x, y, flags, param):
    """Überwacht, ob der User mit der Maus auf unseren gezeichneten Button klickt."""
    global abbruch_geklickt
    if event == cv2.EVENT_LBUTTONDOWN:
        # Koordinaten unseres "Abbrechen"-Buttons (X: 20 bis 160, Y: 20 bis 60)
        if 20 <= x <= 160 and 20 <= y <= 60:
            abbruch_geklickt = True


def scan_and_return_isbn():
    """Öffnet die Kamera mit einem Ziel-Rechteck, scannt EAN-13 und gibt die ISBN zurück."""
    global abbruch_geklickt
    abbruch_geklickt = False  # Beim Start immer zurücksetzen

    cap = cv2.VideoCapture(0)

    # Fenster initialisieren und Maus-Überwachung aktivieren
    fenster_name = "BooktrackQR - Scanner"
    cv2.namedWindow(fenster_name)
    cv2.setMouseCallback(fenster_name, maus_klick_erkennen)

    display_text = "Bitte Barcode in das rote Feld halten..."
    text_color = (0, 0, 0)
    found_isbn = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Dimensionen des Fensters holen
        h, w, _ = frame.shape

        # Ein rotes Ziel-Rechteck in der Mitte zeichnen
        box_w, box_h = 300, 150
        start_x, start_y = int(w / 2 - box_w / 2), int(h / 2 - box_h / 2)
        end_x, end_y = start_x + box_w, start_y + box_h

        # Halbtransparentes Rechteck für den Fokus
        overlay = frame.copy()
        cv2.rectangle(overlay, (start_x, start_y), (end_x, end_y), (0, 0, 255), 3)
        cv2.rectangle(overlay, (start_x - 20, start_y - 20), (end_x + 20, end_y + 20), (0, 0, 255), 1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        # --- NEU: Abbrechen-Button oben links einzeichnen ---
        # Grauer Hintergrund für den Button
        cv2.rectangle(frame, (20, 20), (160, 60), (220, 220, 220), -1)
        # Roter Rand für den Button
        cv2.rectangle(frame, (20, 20), (160, 60), (0, 0, 200), 2)
        # Text im Button
        cv2.putText(frame, "Abbrechen", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        # ----------------------------------------------------

        # Suche nach Barcodes
        barcodes = decode(frame)

        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type

            # Zeichne einen Rahmen um den erkannten Barcode
            (bx, by, bw, bh) = barcode.rect
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (255, 165, 0), 2)

            if barcode_type == 'EAN13' and (barcode_data.startswith('978') or barcode_data.startswith('979')):
                found_isbn = barcode_data
                break
            else:
                display_text = "Falsches Produkt (Keine ISBN)"
                text_color = (0, 0, 255)

        # Schleife abbrechen, wenn eine ISBN gefunden ODER der Button geklickt wurde
        if found_isbn or abbruch_geklickt:
            break

        # Text oben rechts
        font = cv2.FONT_HERSHEY_SIMPLEX
        size = cv2.getTextSize(display_text, font, 0.7, 2)[0]
        x_pos = frame.shape[1] - size[0] - 20
        cv2.putText(frame, display_text, (x_pos, 40), font, 0.7, text_color, 2)

        cv2.imshow(fenster_name, frame)

        # Manuelles Beenden über die Taste 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Manuelles Beenden über das rote 'X' von macOS abfangen (verhindert Abstürze)
        if cv2.getWindowProperty(fenster_name, cv2.WND_PROP_VISIBLE) < 1:
            break

    # Alles sauber schließen
    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # Extra-Sicherheit für macOS, damit das Fenster auch wirklich schließt

    return found_isbn


if __name__ == "__main__":
    print(f"Gescannt: {scan_and_return_isbn()}")