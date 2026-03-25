# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (UniversalScanner Integration)
# Datei: Rueckgabe.py
# ------------------------------------------------------------------------------

import os
import mysql.connector
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# [Ergaenzung]: Import des universellen Scanners
from UniversalQRScanner import UniversalQRScanner


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
        self.in_student.setPlaceholderText("Bitte Schuelerausweis scannen...")
        self.in_student.setReadOnly(True)
        self.in_student.setStyleSheet(
            "padding: 12px; border: 2px solid #000000; border-radius: 6px; "
            "background: #F9F9F9; color: #000000; font-size: 14px; font-weight: bold;")

        self.btn_scan_student = QPushButton("📷 Schueler scannen")
        self.btn_scan_student.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 12px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_student.clicked.connect(self.scan_student)

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
        self.btn_next_student = QPushButton("Nächster Schueler / Reset")
        self.btn_next_student.setStyleSheet(
            "background-color: #CCCCCC; color: #000000; font-weight: bold; padding: 10px; border: 1px solid #000000;")
        self.btn_next_student.clicked.connect(self.reset_view)

        self.btn_scan_book = QPushButton("📷 Buch scannen (Rueckgabe)")
        self.btn_scan_book.setEnabled(False)
        self.btn_scan_book.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 12px 25px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_book.clicked.connect(self.scan_book)

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

    # --- SCAN LOGIK MIT UNIVERSAL SCANNER ---

    def scan_student(self):
        """[Analog zur Ausleihe]: Startet den UniversalQRScanner für Schüler."""
        scanner = UniversalQRScanner(
            parent=self,
            target_mode="STUDENT",
            color_theme=self.COLOR_RED,
            context_text="Schuelerausweis scannen"
        )

        if scanner.exec() == QDialog.DialogCode.Accepted:
            result = scanner.final_result
            if result:
                display = f"{result['vorname']} {result['nachname']}"
                self.in_student.setText(display)
                self.current_student_id = result['db_id']
                self.load_loans_from_db()

    def scan_book(self):
        """[Analog zur Ausleihe]: Startet den UniversalQRScanner für Bücher."""
        scanner = UniversalQRScanner(
            parent=self,
            target_mode="BOOK",
            color_theme=self.COLOR_RED,
            context_text="Buch zur Rückgabe scannen"
        )

        if scanner.exec() == QDialog.DialogCode.Accepted:
            result = scanner.final_result
            if result:
                # Suche das Buch in der aktuellen Tabellenliste
                qr_code_to_find = f"QR-{result['isbn']}-{result['exemplar_nr']}"
                for row in range(self.table.rowCount()):
                    if self.table.item(row, 2).text() == qr_code_to_find:
                        self.process_return_in_db(qr_code_to_find, row)
                        return

                self.zeige_nachricht("Fehler", "Dieses Buch ist nicht in der Ausleihliste des Schülers!",
                                     QMessageBox.Icon.Warning)

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
        except Exception as e:
            self.zeige_nachricht("Fehler", f"Fehler beim Laden: {e}", QMessageBox.Icon.Critical)

    def process_return_in_db(self, qr_code, table_row):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            # Löschen aus der aktuellen Ausleihe
            sql = "DELETE FROM Ausleihe_Aktuell WHERE exemplar_id = (SELECT exemplar_id FROM BuchExemplar WHERE qr_code = %s)"
            cursor.execute(sql, (qr_code,))
            conn.commit()
            conn.close()

            # Tabelleneintrag aktualisieren
            status_item = QTableWidgetItem("✅ Zurueck")
            status_item.setForeground(Qt.GlobalColor.darkGreen)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(table_row, 3, status_item)

            self.zeige_nachricht("Erfolg", f"Buch {qr_code} wurde erfolgreich zurückgegeben.")
        except Exception as e:
            self.zeige_nachricht("DB-Fehler", str(e), QMessageBox.Icon.Critical)

    def reset_view(self):
        self.in_student.clear()
        self.table.setRowCount(0)
        self.btn_scan_book.setEnabled(False)
        self.current_student_id = None