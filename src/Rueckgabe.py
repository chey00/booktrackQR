# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (QR-Erkennung mit validierter Rückmeldung)
# ------------------------------------------------------------------------------

import os
import platform
from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QMessageBox, QDialog, QVBoxLayout, QWidget
)
from PyQt6.QtCore import Qt

# Eigene Module
from base_page import BasePageWidget
from database_manager import DatabaseManager

# Import des Universal Scanners
try:
    from UniversalQRScanner import UniversalQRScanner
except ImportError:
    UniversalQRScanner = None


class RueckgabeWidget(BasePageWidget):
    COLOR_RED = "#E57368"

    def __init__(self, parent=None):
        super().__init__(
            breadcrumb_text="Startseite > Hauptmenü > Rückgabe",
            page_title="Rückgabe",
            accent_color=self.COLOR_RED,
            parent=parent
        )

        self.db_manager = DatabaseManager()
        self.current_student_qr_id = None
        self.active_loans = []
        self.setup_gui()

    def setup_gui(self):
        # --- 1. SCHÜLER-SCAN BEREICH ---
        s_layout = QHBoxLayout()
        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Schülerausweis scannen...")
        self.in_student.setStyleSheet(
            "padding:12px; border:1px solid #CCC; border-radius:8px; color: #000000; font-size: 14px; background: white;")
        self.in_student.setReadOnly(True)

        btn_scan_s = QPushButton("Schüler scannen")
        btn_scan_s.setStyleSheet(self.get_btn_style(self.COLOR_RED))
        btn_scan_s.clicked.connect(self.open_student_scanner)

        s_layout.addWidget(self.in_student, 4)
        s_layout.addWidget(btn_scan_s, 2)
        self.content_layout.addLayout(s_layout)

        self.lbl_status = QLabel("Kein Schüler ausgewählt")
        self.lbl_status.setStyleSheet("color: #000000; font-weight: bold; margin: 10px 0;")
        self.content_layout.addWidget(self.lbl_status)

        # --- 2. BUCH-SCAN BEREICH ---
        b_layout = QHBoxLayout()
        self.in_book = QLineEdit()
        self.in_book.setPlaceholderText("Buch-QR-Code scannen...")
        self.in_book.setStyleSheet(
            "padding:12px; border:1px solid #CCC; border-radius:8px; color: #000000; font-size: 14px; background: white;")
        self.in_book.setReadOnly(True)

        self.btn_scan_b = QPushButton("BUCH SCANNEN")
        self.btn_scan_b.setEnabled(False)
        self.btn_scan_b.setStyleSheet(self.get_btn_style("#CCCCCC"))
        self.btn_scan_b.clicked.connect(self.open_book_scanner)

        b_layout.addWidget(self.in_book, 4)
        b_layout.addWidget(self.btn_scan_b, 2)
        self.content_layout.addLayout(b_layout)

        # --- 3. TABELLE ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ISBN / QR", "Titel", "Aktion"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 100)
        self.table.setMinimumHeight(350)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #DDD; border-radius: 8px; background: white; color: #000000; gridline-color: #EEE; }
            QHeaderView::section { background-color: #F0F0F0; color: #000000; font-weight: bold; border: 1px solid #DDD; }
        """)
        self.content_layout.addWidget(self.table)

        # --- 4. RESET ---
        btn_reset = QPushButton("Zurücksetzen / Neuer Schüler")
        btn_reset.setStyleSheet(
            "background-color: #F0F0F0; color: #000000; padding: 10px; border-radius: 5px; font-weight: bold;")
        btn_reset.clicked.connect(self.reset_view)
        self.content_layout.addWidget(btn_reset)

    def show_message(self, title, text, icon=QMessageBox.Icon.Information, is_question=False):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        if is_question:
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet(
            "QLabel{ color: black; font-weight: bold; } QPushButton{ color: black; background-color: #eee; padding: 5px; } QMessageBox{ background-color: white; }")
        return msg.exec()

    def open_student_scanner(self):
        if not UniversalQRScanner: return
        scanner = UniversalQRScanner(self, target_mode="STUDENT", color_theme=self.COLOR_RED)
        if scanner.exec() == QDialog.DialogCode.Accepted and scanner.final_result:
            sid = scanner.final_result.get('full_id') or scanner.final_result.get('student_id')
            self.in_student.setText(str(sid))
            self.current_student_qr_id = str(sid)
            self.lbl_status.setText(f"✅ AKTIV: {sid}")
            self.btn_scan_b.setEnabled(True)
            self.btn_scan_b.setStyleSheet(self.get_btn_style(self.COLOR_RED))
            self.load_loans()

    def load_loans(self):
        self.active_loans = self.db_manager.get_active_loans_for_student(self.current_student_qr_id)
        self.table.setRowCount(len(self.active_loans))
        for i, row in enumerate(self.active_loans):
            isbn, titel = str(row[0]), str(row[1])
            it0, it1 = QTableWidgetItem(isbn), QTableWidgetItem(titel)
            it0.setForeground(Qt.GlobalColor.black)
            it1.setForeground(Qt.GlobalColor.black)
            self.table.setItem(i, 0, it0)
            self.table.setItem(i, 1, it1)

            btn_delete = QPushButton("Löschen")
            btn_delete.setStyleSheet(
                "background-color: #E57368; color: white; border-radius: 4px; padding: 4px; font-weight: bold;")
            btn_delete.clicked.connect(
                lambda checked, arg_isbn=isbn, arg_titel=titel: self.manual_delete_confirm(arg_isbn, arg_titel))
            self.table.setCellWidget(i, 2, btn_delete)

    def open_book_scanner(self):
        if not UniversalQRScanner: return
        scanner = UniversalQRScanner(self, target_mode="BOOK", color_theme=self.COLOR_RED)

        if scanner.exec() == QDialog.DialogCode.Accepted and scanner.final_result:
            # Extrahiere den gescannten Code
            res = scanner.final_result
            scanned_code = str(
                res.get('book_code') or res.get('qr_code') or res.get('id') or next(iter(res.values()), "")).strip()

            if not scanned_code:
                return

            # SCHRITT 2: Code sofort in das Textfeld schreiben
            self.in_book.setText(scanned_code)

            # Suchen, ob das Buch in der Liste der Ausleihen dieses Schülers existiert
            found_book = next((loan for loan in self.active_loans if str(loan[0]).strip() == scanned_code), None)

            if found_book:
                # Buch ist hinterlegt -> Abfrage zur Rückgabe
                isbn, titel = str(found_book[0]), str(found_book[1])
                frage = f"Soll die Rückgabe von '{titel}' (ISBN: {isbn}) bestätigt werden?\n\nHat der Schüler das Buch abgegeben?"
                if self.show_message('Rückgabe bestätigen', frage, QMessageBox.Icon.Question,
                                     True) == QMessageBox.StandardButton.Yes:
                    self.execute_deletion(isbn)
            else:
                # Buch ist nicht in der Liste des Schülers -> Fehlermeldung wie gewünscht
                self.show_message("Rückgabe fehlgeschlagen",
                                  "Dieses Buch gehört nicht dem Schüler.",
                                  QMessageBox.Icon.Critical)
                # Textfeld leeren, da das Buch nicht gültig für diesen Schüler ist
                self.in_book.clear()

    def manual_delete_confirm(self, isbn, titel):
        frage = f"Soll das Buch '{titel}' wirklich von diesem Schüler zurückgegeben werden?"
        if self.show_message('Manuelle Rückgabe', frage, QMessageBox.Icon.Question,
                             True) == QMessageBox.StandardButton.Yes:
            self.execute_deletion(isbn)

    def execute_deletion(self, isbn):
        if self.db_manager.return_book_by_isbn(self.current_student_qr_id, isbn):
            self.show_message("Erfolg", f"Die Rückgabe wurde erfolgreich verbucht.")
            self.load_loans()
            self.in_book.clear()
        else:
            self.show_message("Fehler", "Der Datensatz konnte nicht in der Datenbank aktualisiert werden.",
                              QMessageBox.Icon.Warning)

    def reset_view(self):
        self.in_student.clear();
        self.in_book.clear();
        self.table.setRowCount(0)
        self.lbl_status.setText("Kein Schüler ausgewählt")
        self.btn_scan_b.setEnabled(False);
        self.btn_scan_b.setStyleSheet(self.get_btn_style("#CCCCCC"))
        self.current_student_qr_id = None
        self.active_loans = []

    def get_btn_style(self, color):
        return f"background-color: {color}; color: white; padding: 12px; font-weight: bold; border-radius: 8px;"