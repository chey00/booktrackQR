# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (ROBUSTE CSV-SUCHE)
# Datei: Rueckgabe.py
# ------------------------------------------------------------------------------

import os
import cv2
import csv
import mysql.connector
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Pfad zu deiner Schülerliste
CSV_PFAD = "schuelerlisten/Testdaten Schüler.csv"


class RueckgabeWidget(QWidget):
    COLOR_RED = "#E57368"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_config = {
            'host': '192.168.10.195', 'port': 3306,
            'user': 'bookuser', 'password': '12345678', 'database': 'DB_BooktrackQR'
        }
        self.current_student_id = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 45, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(header_layout)

        breadcrumb = QLabel("Startseite > Hauptmenü > Rückgabe")
        breadcrumb.setStyleSheet("color: #000000; font-weight: bold;")
        main_layout.addWidget(breadcrumb)

        page_title = QLabel("Rückgabe-Modul")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {self.COLOR_RED};")
        main_layout.addWidget(page_title)

        # Scan Bereich
        scan_area = QHBoxLayout()
        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Bitte Schülerausweis scannen (CSV/DB)...")
        self.in_student.setReadOnly(True)
        self.in_student.setStyleSheet(
            "padding: 12px; border: 2px solid #000000; border-radius: 6px; "
            "background: #F9F9F9; color: #000000; font-size: 14px; font-weight: bold;")

        self.btn_scan_student = QPushButton("📷 Schüler scannen")
        self.btn_scan_student.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 12px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_student.clicked.connect(self.scan_student_with_camera)

        scan_area.addWidget(self.in_student)
        scan_area.addWidget(self.btn_scan_student)
        main_layout.addLayout(scan_area)

        # Tabelle
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ISBN", "Buchtitel", "Exemplar-ID / QR", "Status"])
        self.table.setStyleSheet("""
            QTableWidget { border: 2px solid #000000; gridline-color: #000000; color: #000000; font-weight: bold; }
            QHeaderView::section { background-color: #E0E0E0; border: 1px solid #000000; font-weight: bold; color: #000000; }
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 150)
        main_layout.addWidget(self.table)

        # Aktionen
        actions_layout = QHBoxLayout()
        self.btn_next_student = QPushButton("Nächster Schüler / Reset")
        self.btn_next_student.setStyleSheet(
            "background-color: #CCCCCC; color: #000000; font-weight: bold; padding: 10px; border: 1px solid #000000;")
        self.btn_next_student.clicked.connect(self.reset_view)

        self.btn_scan_book = QPushButton("📷 Buch scannen (Rückgabe)")
        self.btn_scan_book.setEnabled(False)
        self.btn_scan_book.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 12px 25px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_book.clicked.connect(self.scan_book_return_with_camera)

        actions_layout.addWidget(self.btn_next_student)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_scan_book)
        main_layout.addLayout(actions_layout)

        # Zurück Button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.zurueck_btn = QPushButton("⬅ Zurück zum Hauptmenü")
        self.zurueck_btn.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 25px; font-weight: bold; border-radius: 6px;")
        footer_layout.addWidget(self.zurueck_btn)
        main_layout.addLayout(footer_layout)

    def zeige_nachricht(self, titel, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setWindowTitle(titel)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet(
            "QLabel { color: #000000; font-weight: bold; font-size: 14px; } QPushButton { color: #000000; font-weight: bold; }")
        msg.exec()

    # --- VERBESSERTE CSV LOGIK ---
    def suche_schueler_in_csv(self, scanned_id):
        if not os.path.exists(CSV_PFAD):
            return None

        try:
            # Wir versuchen es erst mit Semikolon (Standard Excel-DE)
            with open(CSV_PFAD, mode='r', encoding='utf-8-sig') as f:
                # Automatisches Erkennen des Trennzeichens
                content = f.read(2048)
                f.seek(0)
                dialect = csv.Sniffer().sniff(content, delimiters=";,")
                reader = csv.DictReader(f, dialect=dialect)

                for row in reader:
                    # Wir strippen Leerzeichen und vergleichen Case-Insensitive
                    for key, value in row.items():
                        if key and ("id" in key.lower() or "studierende" in key.lower()):
                            if str(value).strip().lower() == str(scanned_id).strip().lower():
                                vorname = row.get('vorname', '') or row.get('Vorname', '')
                                nachname = row.get('nachname', '') or row.get('Nachname', '')
                                return f"{vorname} {nachname}".strip()
        except Exception as e:
            print(f"CSV-Fehler: {e}")
            return None
        return None

    def scan_student_with_camera(self):
        scanned_id = self._get_qr_from_camera("Schueler scannen (CSV/DB)...")
        if scanned_id:
            name = self.suche_schueler_in_csv(scanned_id)

            if not name:
                try:
                    conn = mysql.connector.connect(**self.db_config)
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT vorname, nachname FROM Studierende WHERE studierende_id = %s", (scanned_id,))
                    res = cursor.fetchone()
                    conn.close()
                    if res: name = f"{res['vorname']} {res['nachname']}"
                except:
                    pass

            if name:
                self.in_student.setText(f"{scanned_id} - {name}")
                self.current_student_id = scanned_id
                self.load_loans_from_db()
            else:
                self.zeige_nachricht("Nicht gefunden",
                                     f"ID {scanned_id} wurde weder in der CSV noch in der DB gefunden.",
                                     QMessageBox.Icon.Warning)

    def _get_qr_from_camera(self, instruction_text):
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()
        result = None
        while True:
            ret, frame = cap.read()
            if not ret: break
            cv2.putText(frame, instruction_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                result = data
                break
            cv2.imshow("Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
        cap.release()
        cv2.destroyAllWindows()
        return result

    def load_loans_from_db(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            query = "SELECT isbn, titel, qr_code FROM v_studierende_ausleihen WHERE studierende_id = %s"
            cursor.execute(query, (self.current_student_id,))
            books = cursor.fetchall()
            conn.close()
            self.table.setRowCount(len(books))
            for row, book in enumerate(books):
                cols = [str(book['isbn']), str(book['titel']), str(book['qr_code']), "Ausgeliehen"]
                for col_idx, text in enumerate(cols):
                    item = QTableWidgetItem(text)
                    item.setForeground(Qt.GlobalColor.black)
                    self.table.setItem(row, col_idx, item)
            self.btn_scan_book.setEnabled(True)
        except:
            pass

    def scan_book_return_with_camera(self):
        scanned_code = self._get_qr_from_camera("Buch scannen...")
        if scanned_code:
            clean_code = scanned_code.split('|')[-1] if '|' in scanned_code else scanned_code
            for row in range(self.table.rowCount()):
                if self.table.item(row, 2).text() == clean_code:
                    self.process_return_in_db(clean_code, row)
                    return
            self.zeige_nachricht("Fehler", "Buch gehört nicht zu diesem Schüler!", QMessageBox.Icon.Warning)

    def process_return_in_db(self, qr_code, table_row):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            sql = "DELETE FROM Ausleihe_Aktuell WHERE exemplar_id = (SELECT exemplar_id FROM BuchExemplar WHERE qr_code = %s)"
            cursor.execute(sql, (qr_code,))
            conn.commit()
            conn.close()
            self.table.setItem(table_row, 3, QTableWidgetItem("✅ Zurück"))
            self.zeige_nachricht("Erfolg", f"Buch {qr_code} zurückgegeben.")
        except:
            pass

    def reset_view(self):
        self.in_student.clear()
        self.table.setRowCount(0)
        self.btn_scan_book.setEnabled(False)