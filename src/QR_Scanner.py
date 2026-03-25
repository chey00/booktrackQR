# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: QR_Scanner (Fix: Relative Pfade & Super Clean)
# Autoren: Harun Kayaci, Jaclyn Barta
# ------------------------------------------------------------------------------
import cv2
import csv
import os
import mysql.connector
import openpyxl
import re

# --- KONFIGURATION DER PFADE ---
# Da die Datei im Ordner 'src' liegt, springen wir mit '..' eine Ebene höher
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX_PFAD = os.path.join(BASE_DIR, "schuelerlisten", "Testdaten Schüler.xlsx")
CSV_PFAD = os.path.join(BASE_DIR, "schuelerlisten", "Testdaten Schüler.csv")

DB_CONFIG = {
    'host': '192.168.10.195',
    'port': 3306,
    'user': 'bookuser',
    'password': '12345678',
    'database': 'DB_BooktrackQR'
}


def super_clean(val):
    """Bereinigt IDs von Leerzeichen und Sonderzeichen."""
    if val is None: return ""
    s = str(val).strip().upper()
    return re.sub(r'[^A-Z0-9\-_]', '', s)


def suche_daten(scanned_id):
    """Sucht die ID in Excel, CSV und DB und gibt den Namen zurück."""
    s_id = super_clean(scanned_id)
    if not s_id: return None

    # 1. EXCEL CHECK
    if os.path.exists(XLSX_PFAD):
        try:
            wb = openpyxl.load_workbook(XLSX_PFAD, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if super_clean(row[0]) == s_id:
                    return f"{row[1]} {row[2]} (Excel)"
        except:
            pass

    # 2. CSV CHECK
    if os.path.exists(CSV_PFAD):
        try:
            with open(CSV_PFAD, mode='r', encoding='utf-8-sig') as f:
                content = f.read(2048)
                f.seek(0)
                dialect = csv.Sniffer().sniff(content, delimiters=";,")
                reader = csv.DictReader(f, dialect=dialect)
                for row in reader:
                    for k, v in row.items():
                        if k and "id" in k.lower() and super_clean(v) == s_id:
                            vn = row.get('vorname') or row.get('Vorname') or ""
                            nn = row.get('nachname') or row.get('Nachname') or ""
                            return f"{vn} {nn} (CSV)"
        except:
            pass

    # 3. DB CHECK
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT vorname, nachname FROM Studierende WHERE studierende_id = %s", (scanned_id,))
        res = cursor.fetchone()
        conn.close()
        if res: return f"{res[0]} {res[1]} (DB)"
    except:
        pass

    return "NICHT GEFUNDEN"


def run_scanner():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    # Letztes Ergebnis speichern, um es dauerhaft anzuzeigen
    display_text = "Warte auf Scan..."
    text_color = (0, 0, 0)  # Schwarz

    print("Scanner gestartet. Drücke 'q' zum Beenden.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # QR-Code suchen
        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            print(f"Scan erkannt: {data}")
            name = suche_daten(data)
            if name and name != "NICHT GEFUNDEN":
                display_text = f"Gefunden: {name}"
                text_color = (0, 150, 0)  # Dunkelgrün bei Erfolg
            else:
                display_text = f"ID {data} unbekannt!"
                text_color = (0, 0, 255)  # Rot bei Fehler

        # --- TEXT OBEN RECHTS POSITIONIEREN ---
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.7
        thick = 2
        # Größe des Textes berechnen für rechtsbündige Ausrichtung
        size = cv2.getTextSize(display_text, font, scale, thick)[0]
        x_pos = frame.shape[1] - size[0] - 20
        y_pos = 40

        # Text zeichnen
        cv2.putText(frame, display_text, (x_pos, y_pos), font, scale, text_color, thick)

        cv2.imshow("BooktrackQR Standalone Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_scanner()