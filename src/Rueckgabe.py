# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (Design-Matching Bild 1 + Schwarze Schrift)
# Datei: Rueckgabe.py
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from app_paths import resource_path_any
from UniversalQRScanner import UniversalQRScanner
from database_manager import DatabaseManager


class RueckgabeWidget(QWidget):
    COLOR_RED = "#E57368"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.current_student_qr_id = None

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Global für dieses Widget: Hintergrund weiß, Schrift schwarz
        self.setStyleSheet("background-color: #FFFFFF; color: #000000;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(80, 40, 80, 40)
        outer_layout.setSpacing(10)

        # --- 1. HEADER ---
        header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 52, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; border: none;")  # Dunkelgrau/Schwarz
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = resource_path_any(os.path.join("pic", "technikerschule_logo.png"),
                                      os.path.join("..", "pic", "technikerschule_logo.png"))
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)
        outer_layout.addLayout(header_layout)

        # --- 2. TITEL & BREADCRUMBS ---
        breadcrumb = QLabel("Startseite > Hauptmenü > Rückgabe")
        breadcrumb.setStyleSheet("color: #666666; font-style: italic; font-size: 14px;")
        outer_layout.addWidget(breadcrumb)

        page_title = QLabel("Rückgabe")
        page_title.setFont(QFont("Open Sans", 28, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {self.COLOR_RED};")
        outer_layout.addWidget(page_title)

        hint = QLabel(
            "Ablauf: Schüler scannen oder ID eingeben -> ausgeliehene Bücher anzeigen -> Buch scannen/eingeben -> Zustand auswählen -> Rückgabe übernehmen.")
        hint.setStyleSheet("color: #000000; font-size: 14px;")  # Explizit schwarz
        outer_layout.addWidget(hint)

        # --- 3. INPUTS ---
        # Schüler
        student_line = QHBoxLayout()
        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Schüler-ID eingeben oder scannen...")
        self.in_student.setMinimumHeight(45)
        # color: #000000 erzwingt schwarze Schrift beim Tippen
        self.in_student.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 5px; font-size: 15px; background: white; color: #000000;")

        btn_apply_student = QPushButton("Übernehmen")
        btn_apply_student.setMinimumHeight(45)
        btn_apply_student.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 0 20px; font-weight: bold; border-radius: 5px;")
        btn_apply_student.clicked.connect(self.manual_student_enter)

        self.btn_scan_student = QPushButton("Schülerausweis scannen")
        self.btn_scan_student.setMinimumHeight(45)
        self.btn_scan_student.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 0 20px; font-weight: bold; border-radius: 5px;")
        self.btn_scan_student.clicked.connect(self.scan_student)

        student_line.addWidget(self.in_student, stretch=4)
        student_line.addWidget(btn_apply_student, stretch=1)
        student_line.addWidget(self.btn_scan_student, stretch=1)
        student_line.addStretch(2)
        outer_layout.addLayout(student_line)

        # Buch
        book_line = QHBoxLayout()
        self.in_book = QLineEdit()
        self.in_book.setPlaceholderText("Buchcode/ISBN eingeben oder scannen...")
        self.in_book.setMinimumHeight(45)
        self.in_book.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 5px; font-size: 15px; background: white; color: #000000;")
        self.in_book.setEnabled(False)

        btn_apply_book = QPushButton("Übernehmen")
        btn_apply_book.setMinimumHeight(45)
        btn_apply_book.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 0 20px; font-weight: bold; border-radius: 5px;")
        btn_apply_book.clicked.connect(self.manual_book_enter)

        self.btn_scan_book = QPushButton("QR-Code scannen")
        self.btn_scan_book.setMinimumHeight(45)
        self.btn_scan_book.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 0 20px; font-weight: bold; border-radius: 5px;")
        self.btn_scan_book.setEnabled(False)
        self.btn_scan_book.clicked.connect(self.scan_book)

        book_line.addWidget(self.in_book, stretch=4)
        book_line.addWidget(btn_apply_book, stretch=1)
        book_line.addWidget(self.btn_scan_book, stretch=1)
        book_line.addStretch(2)
        outer_layout.addLayout(book_line)

        # --- 4. TABELLE ---
        lbl_info = QLabel("Aktuell ausgeliehene / offene Rückgaben des ausgewählten Schülers:")
        lbl_info.setStyleSheet("color: #000000; font-weight: bold; margin-top: 20px;")
        outer_layout.addWidget(lbl_info)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Buchcode", "ISBN", "Titel", "Zustand"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # color: #000000 in QTableWidget und HeaderView erzwingt Schwarz
        self.table.setStyleSheet(f"""
            QTableWidget {{ 
                border: 1px solid {self.COLOR_RED}; 
                border-radius: 5px; 
                gridline-color: #F2F2F2;
                background-color: #FFFFFF;
                color: #000000;
            }}
            QHeaderView::section {{ 
                background-color: #F8F8F8; 
                color: #000000; 
                padding: 10px; 
                font-weight: bold; 
                border: none;
                border-bottom: 2px solid {self.COLOR_RED}; 
            }}
        """)
        outer_layout.addWidget(self.table)

        # --- 5. AKTIONEN ---
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.btn_reset = QPushButton("Zurücksetzen")
        self.btn_reset.setStyleSheet(
            "background-color: #E0E0E0; color: #000000; padding: 10px 25px; border-radius: 5px; font-weight: bold;")
        self.btn_reset.clicked.connect(self.reset_view)

        self.btn_finish = QPushButton("Rückgabe abschließen")
        self.btn_finish.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 25px; border-radius: 5px; font-weight: bold;")
        self.btn_finish.clicked.connect(self.reset_view)

        bottom_row.addWidget(self.btn_reset)
        bottom_row.addWidget(self.btn_finish)
        outer_layout.addLayout(bottom_row)

        # --- 6. NAV ---
        nav_row = QHBoxLayout()
        nav_row.addStretch()
        self.zurueck_btn = QPushButton("⬅ Zurück zum Hauptmenü")
        self.zurueck_btn.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 30px; border-radius: 5px; font-weight: bold;")
        nav_row.addWidget(self.zurueck_btn)
        outer_layout.addLayout(nav_row)

    # --- LOGIK (Bleibt gleich) ---
    def manual_student_enter(self):
        sid = self.in_student.text().strip()
        if sid: self._process_student(sid)

    def _process_student(self, qr_id):
        student = self.db_manager.get_student_by_qr_id(qr_id)
        if student:
            self.current_student_qr_id = qr_id
            self.in_student.setText(f"{student['full_id']} - {student['vorname']} {student['nachname']}")
            self.in_book.setEnabled(True)
            self.btn_scan_book.setEnabled(True)
            self.load_loans()

    def load_loans(self):
        loans = self.db_manager.get_active_loans_for_student(self.current_student_qr_id)
        self.table.setRowCount(len(loans))
        for i, r in enumerate(loans):
            # QTableWidgetItem bekommt explizit schwarze Schrift
            it0 = QTableWidgetItem("-")
            it1 = QTableWidgetItem(str(r[0]))
            it2 = QTableWidgetItem(str(r[1]))
            it3 = QTableWidgetItem("Normal")
            for item in [it0, it1, it2, it3]:
                item.setForeground(Qt.GlobalColor.black)
            self.table.setItem(i, 0, it0)
            self.table.setItem(i, 1, it1)
            self.table.setItem(i, 2, it2)
            self.table.setItem(i, 3, it3)

    def scan_student(self):
        scanner = UniversalQRScanner(parent=self, target_mode="STUDENT", color_theme=self.COLOR_RED,
                                     context_text="Schuelerausweis scannen")
        if scanner.exec() == QDialog.DialogCode.Accepted and scanner.final_result:
            self._process_student(scanner.final_result['full_id'])

    def manual_book_enter(self):
        isbn = self.in_book.text().strip()
        if isbn: self._process_book(isbn)

    def _process_book(self, isbn):
        if self.db_manager.return_book_by_isbn(self.current_student_qr_id, isbn):
            QMessageBox.information(self, "Erfolg", f"Buch {isbn} zurückgegeben.")
            self.load_loans()

    def scan_book(self):
        scanner = UniversalQRScanner(parent=self, target_mode="BOOK", color_theme=self.COLOR_RED,
                                     context_text="Buch zur Rückgabe scannen")
        if scanner.exec() == QDialog.DialogCode.Accepted and scanner.final_result:
            self._process_book(scanner.final_result['isbn'])

    def reset_view(self):
        self.in_student.clear()
        self.in_book.clear()
        self.in_book.setEnabled(False)
        self.btn_scan_book.setEnabled(False)
        self.table.setRowCount(0)
        self.current_student_qr_id = None