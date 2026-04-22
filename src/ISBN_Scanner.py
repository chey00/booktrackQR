# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: ISBN_Scanner (PBI 10.1.1 & Integration)
# Autoren: Mustafa Demiral, Ahmet Toplar
# Beschreibung: Robuster Scanner mittels ZXing (OHNE pyzbar, OHNE Mac-Terminal-Zwang).
# Fix: Format-Check gelockert, erkennt jetzt zuverlässig jede 978/979 ISBN.
# ------------------------------------------------------------------------------
import cv2
import re
import zxingcpp
from PyQt6.QtWidgets import QMessageBox

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

    # --- NEU: macOS Sicherheits-Check --- Daniel Popp
    if not cap.isOpened():
        msg = QMessageBox()
        msg.setStyleSheet(
            "QMessageBox { background-color: #FFFFFF; } QLabel { color: #000000; font-size: 14px; } QPushButton { color: #000000; background-color: #E0E0E0; border-radius: 5px; padding: 5px 15px; }")

        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Kamera-Zugriff")
        msg.setText("Kamera wird initialisiert oder ist durch macOS blockiert.")
        msg.setInformativeText(
            "Falls macOS gerade nach der Berechtigung gefragt hat: Bitte klicken Sie auf 'Erlauben' und starten Sie den Scanner danach einfach noch einmal.")
        msg.exec()
        cap.release()
        return None
    # ------------------------------------

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

        # --- Abbrechen-Button ---
        cv2.rectangle(frame, (20, 20), (160, 60), (220, 220, 220), -1)
        cv2.rectangle(frame, (20, 20), (160, 60), (0, 0, 200), 2)
        cv2.putText(frame, "Abbrechen", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # --- Barcode lesen mit ZXing ---
        results = zxingcpp.read_barcodes(frame)

        for result in results:
            raw_data = result.text

            # Zeichne einen blauen Rahmen um den erkannten Barcode
            try:
                p = result.position
                cv2.line(frame, (p.top_left.x, p.top_left.y), (p.top_right.x, p.top_right.y), (255, 165, 0), 2)
                cv2.line(frame, (p.top_right.x, p.top_right.y), (p.bottom_right.x, p.bottom_right.y), (255, 165, 0), 2)
                cv2.line(frame, (p.bottom_right.x, p.bottom_right.y), (p.bottom_left.x, p.bottom_left.y), (255, 165, 0),
                         2)
                cv2.line(frame, (p.bottom_left.x, p.bottom_left.y), (p.top_left.x, p.top_left.y), (255, 165, 0), 2)
            except Exception:
                pass

            # Zahlen filtern (falls unsichtbare Sonderzeichen dabei sind)
            clean_digits = re.sub(r'\D', '', raw_data)

            # FIX: Wir prüfen nur noch, ob die Nummer wie eine ISBN aussieht (13 Zahlen, beginnt mit 978/979)
            if len(clean_digits) >= 13 and (clean_digits.startswith('978') or clean_digits.startswith('979')):
                found_isbn = clean_digits[:13]
                break
            else:
                display_text = f"Falsches Produkt erkannt: {clean_digits}"
                text_color = (0, 0, 255)

        if found_isbn or abbruch_geklickt:
            break

        # Text oben rechts
        font = cv2.FONT_HERSHEY_SIMPLEX
        size = cv2.getTextSize(display_text, font, 0.7, 2)[0]
        x_pos = frame.shape[1] - size[0] - 20
        cv2.putText(frame, display_text, (x_pos, 40), font, 0.7, text_color, 2)

        cv2.imshow(fenster_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if cv2.getWindowProperty(fenster_name, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)

    return found_isbn


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    print(f"Gescannt: {scan_and_return_isbn()}")