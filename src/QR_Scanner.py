# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: QR_Scanner (Echtzeit-Abgleich mit MariaDB auf Raspberry Pi)
# Datei: QR_Scanner.py
#
# Autoren: Ahmet Topler & Jaclyn Barta
#
# - Ahmet Topler: Initiale Kamera-Ansteuerung (OpenCV), Basis-Schleife,
#                 CSV-Logging-Funktion, Grundgerüst des PyQt6-Popups.
# - Jaclyn Barta: Netzwerk-Konfiguration (MariaDB), SQL-Join-Logik (ISBN-Abgleich),
#                 String-Parsing (Zerlegung BOOK|ISBN|Ex), PBI-Fehlerhandling
#                 (Unscharf-Meldung), Stabilitäts-Fixes für macOS & Hardware-Timing.
#
# Stand vorher: (Rene Bezold & Jaclyn Barta)
# - Abgleich erfolgte gegen lokale Bilddateien im Ordner "qr_pic" (Whitelist).
# - Keine Verbindung zu einer externen Datenbank.
# - Einfache Statusmeldung ohne Detail-Infos zur ISBN.
#
# Stand jetzt (Angepasst):
# - PBI Erfüllung: QR-Code Abgleich ohne lokales Bild direkt über MariaDB.
# - Automatisches Parsing: Extrahiert ISBN aus komplexen QR-Strings.
# - Dynamische UI: Zeigt spezifische Fehlermeldungen inkl. gescannter ISBN an.
# - Robustes System: Erkennt unscharfe/verdeckte Codes laut User Story.
# ------------------------------------------------------------------------------

import cv2
import mysql.connector
import time
import csv
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

# --- EINSTELLUNGEN ---
# Erstellt von: Ahmet Topler & Jaclyn Barta
LOG_FILE = "scan_historie.csv"
BRAND_GREEN = "#008781"


def check_qr_in_db(scanned_code, db_config):
    """
    Entwickelt von: Jaclyn Barta
    Zerlegt den QR-String (BOOK|ISBN|Exemplar) und prüft
    über einen JOIN, ob das Exemplar in der DB existiert.
    Gibt (Erfolg, ISBN/Fehlermeldung) zurück.
    """
    try:
        # String zerlegen: Jaclyn Barta
        teile = scanned_code.split('|')
        if len(teile) < 2:
            return False, "Format ungültig"

        isbn_aus_qr = teile[1]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # SQL-Join Logik: Jaclyn Barta
        query = """
            SELECT e.exemplar_id 
            FROM BuchExemplar e
            JOIN BuchTitel t ON e.titel_id = t.titel_id
            WHERE t.isbn = %s
        """
        cursor.execute(query, (isbn_aus_qr,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return True, isbn_aus_qr
        else:
            return False, isbn_aus_qr

    except Exception as e:
        return False, f"DB-Fehler: {e}"


def speichere_scan(inhalt):
    """
    Entwickelt von: Ahmet Topler
    Speichert erfolgreiche Scans in der CSV.
    """
    datei_existiert = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not datei_existiert:
            writer.writerow(["Datum", "Uhrzeit", "Inhalt"])
        jetzt = datetime.now()
        writer.writerow([jetzt.strftime("%d.%m.%Y"), jetzt.strftime("%H:%M:%S"), inhalt])


def zeige_pyqt_popup(app_instance, qr_daten):
    """
    Entwickelt von: Ahmet Topler & Jaclyn Barta
    Zeigt Erfolgs-Popup nach einem Fund.
    """
    window = QWidget()
    window.setWindowTitle("Scan Status")
    window.setFixedSize(400, 230)
    window.setStyleSheet("background-color: white;")
    window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    layout = QVBoxLayout()
    label_titel = QLabel("SCAN ERFOLGREICH")
    label_titel.setStyleSheet(f"color: {BRAND_GREEN}; font-size: 22px; font-weight: bold;")
    label_msg = QLabel(f"Exemplar zur ISBN gefunden:\n{qr_daten}")
    label_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

    btn = QPushButton("OK")
    btn.setFixedWidth(140)
    btn.setStyleSheet(
        f"background-color: {BRAND_GREEN}; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
    btn.clicked.connect(window.close)

    layout.addWidget(label_titel, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label_msg, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    window.setLayout(layout)
    window.show()
    app_instance.exec()


def run_scanner(app_instance, db_config):
    """
    Entwickelt von: Ahmet Topler & Jaclyn Barta
    Haupt-Loop für Kamera und Abgleich.
    """
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    gescannter_inhalt = None

    print("Kamera gestartet. Suche nach QR-Codes...")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        data, bbox, _ = detector.detectAndDecode(frame)

        status_text = "Suche QR Code..."
        color = (200, 200, 200)

        if data:
            # Abgleich-Logik: Jaclyn Barta
            success, info = check_qr_in_db(data, db_config)

            if success:
                status_text = f"ERFOLG: ISBN {info} gefunden!"
                color = (0, 255, 0)
                gescannter_inhalt = data
                speichere_scan(data)
            else:
                status_text = f"KEIN EXEMPLAR: ISBN {info} unbekannt!"
                color = (0, 0, 255)

        elif bbox is not None and len(bbox) > 0:
            # PBI Anforderung: Jaclyn Barta
            status_text = "BITTE ERNEUT SCANNEN (UNSCHARF)"
            color = (0, 165, 255)

        # UI Anzeige: Ahmet Topler & Jaclyn Barta
        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imshow('BooktrackQR Scanner', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if gescannter_inhalt:
            cv2.waitKey(1500)
            break

    cap.release()
    cv2.destroyAllWindows()
    return gescannter_inhalt


if __name__ == '__main__':
    # Start-Konfiguration und Netzwerk-Test: Jaclyn Barta
    app = QApplication(sys.argv)

    config = {
        'host': '192.168.10.195',
        'port': 3306,
        'user': 'bookuser',
        'password': '12345678',
        'database': 'DB_BooktrackQR'
    }

    try:
        test_conn = mysql.connector.connect(**config)
        print("Python-Verbindung zum Pi erfolgreich! ✅")
        test_conn.close()

        ergebnis = run_scanner(app, config)

        if ergebnis:
            zeige_pyqt_popup(app, ergebnis)

    except Exception as e:
        print(f"❌ Initialer Verbindungsfehler: {e}")
import cv2
import mysql.connector
import time
import csv
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

# --- EINSTELLUNGEN ---
# Erstellt von: Ahmet Topler & Jaclyn Barta (Initiales Projekt-Setup)
LOG_FILE = "scan_historie.csv"
BRAND_GREEN = "#008781"


def check_qr_in_db(scanned_code, db_config):
    """
    Entwickelt von: Jaclyn Barta (Wirtschaftsinformatik-Fokus)
    Zerlegt den QR-String (BOOK|ISBN|Exemplar) und prüft
    über einen JOIN, ob das Exemplar in der DB existiert.
    Gibt (Erfolg, ISBN/Fehlermeldung) zurück.
    """
    try:
        # String zerlegen: Jaclyn Barta (Anpassung an QR-Struktur)
        teile = scanned_code.split('|')
        if len(teile) < 2:
            return False, "Format ungültig"

        isbn_aus_qr = teile[1]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # SQL-Join Logik: Jaclyn Barta (Anbindung an MariaDB & Datenmodellierung)
        query = """
            SELECT e.exemplar_id 
            FROM BuchExemplar e
            JOIN BuchTitel t ON e.titel_id = t.titel_id
            WHERE t.isbn = %s
        """
        cursor.execute(query, (isbn_aus_qr,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return True, isbn_aus_qr
        else:
            return False, isbn_aus_qr

    except Exception as e:
        return False, f"DB-Fehler: {e}"


def speichere_scan(inhalt):
    """
    Entwickelt von: Ahmet Topler (Basis-Historienfunktion)
    Speichert erfolgreiche Scans in der CSV.
    """
    datei_existiert = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not datei_existiert:
            writer.writerow(["Datum", "Uhrzeit", "Inhalt"])
        jetzt = datetime.now()
        writer.writerow([jetzt.strftime("%d.%m.%Y"), jetzt.strftime("%H:%M:%S"), inhalt])


def zeige_pyqt_popup(app_instance, qr_daten):
    """
    Entwickelt von: Ahmet Topler (Basis-UI) & Jaclyn Barta (Anpassung Datenanzeige)
    Zeigt Erfolgs-Popup nach einem Fund.
    """
    window = QWidget()
    window.setWindowTitle("Scan Status")
    window.setFixedSize(400, 230)
    window.setStyleSheet("background-color: white;")
    window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    layout = QVBoxLayout()
    label_titel = QLabel("SCAN ERFOLGREICH")
    label_titel.setStyleSheet(f"color: {BRAND_GREEN}; font-size: 22px; font-weight: bold;")
    label_msg = QLabel(f"Exemplar zur ISBN gefunden:\n{qr_daten}")
    label_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

    btn = QPushButton("OK")
    btn.setFixedWidth(140)
    btn.setStyleSheet(
        f"background-color: {BRAND_GREEN}; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
    btn.clicked.connect(window.close)

    layout.addWidget(label_titel, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label_msg, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    window.setLayout(layout)
    window.show()
    app_instance.exec()


def run_scanner(app_instance, db_config):
    """
    Entwickelt von: Ahmet Topler (Basis-Loop) & Jaclyn Barta (PBI Fehler-Logik & DB-Validierung)
    Haupt-Loop für Kamera und Abgleich.
    """
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    gescannter_inhalt = None

    print("Kamera gestartet. Suche nach QR-Codes...")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        data, bbox, _ = detector.detectAndDecode(frame)

        status_text = "Suche QR Code..."
        color = (200, 200, 200)

        if data:
            # Abgleich-Logik: Jaclyn Barta (Implementierung User Story)
            success, info = check_qr_in_db(data, db_config)

            if success:
                status_text = f"ERFOLG: ISBN {info} gefunden!"
                color = (0, 255, 0)
                gescannter_inhalt = data
                speichere_scan(data)
            else:
                status_text = f"KEIN EXEMPLAR: ISBN {info} unbekannt!"
                color = (0, 0, 255)

        # Fehlerfall-Anpassung: Jaclyn Barta (PBI: Unscharf/Verdeckt)
        elif bbox is not None and len(bbox) > 0:
            status_text = "BITTE ERNEUT SCANNEN (UNSCHARF)"
            color = (0, 165, 255)

        # UI-Rendering: Ahmet Topler & Jaclyn Barta
        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imshow('BooktrackQR Scanner', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if gescannter_inhalt:
            cv2.waitKey(1500)
            break

    cap.release()
    cv2.destroyAllWindows()
    return gescannter_inhalt


if __name__ == '__main__':
    # Gesamte Start-Konfiguration und Test-Logik: Jaclyn Barta
    app = QApplication(sys.argv)

    config = {
        'host': '192.168.10.195',
        'port': 3306,
        'user': 'bookuser',
        'password': '12345678',
        'database': 'DB_BooktrackQR'
    }

    try:
        test_conn = mysql.connector.connect(**config)
        print("Python-Verbindung zum Pi erfolgreich! ✅")
        test_conn.close()

        ergebnis = run_scanner(app, config)

        if ergebnis:
            zeige_pyqt_popup(app, ergebnis)

    except Exception as e:
        print(f"❌ Initialer Verbindungsfehler: {e}")