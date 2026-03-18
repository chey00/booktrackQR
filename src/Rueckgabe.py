# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (GUI Design & Schüler-Buchliste Erweiterung)
# Datei: Rueckgabe.py
#
# Autorin: Jaclyn Barta (PBI 3.5.1 Erweiterung & Refactoring)
#
# Stand vorher (Rene Bezold & Jaclyn Barta):
# - Statisches Layout mit einer festen Kamera-Box ohne echte Funktion.
# - Keine Verknüpfung zwischen Schüler-Daten und den dazugehörigen Büchern.
# - Nur visuelle Platzhalter für den Scan-Vorgang.
#
# Stand nachher (Angepasst durch Jaclyn Barta):
# - PBI 3.5.1 Erfüllung: Rückgabe-Ansicht um interaktiven Schüler-Scan erweitert.
# - Dynamische Buchliste: Nach Schüler-Scan wird die Liste der ausgeliehenen
#   Bücher geladen und in der Tabelle visualisiert (Dummy-Daten für Demo).
# - "Nächster Schüler"-Funktion: Vollständiger Reset der Ansicht und der Tabelle.
# - Rückgabe-Logik: "Buch scannen (Rückgabe)" prüft die ISBN gegen die geladene
#   Liste und aktualisiert den Status live in der Tabelle auf "Zurückgegeben".
# - UI/UX: Anpassung an das Design der Ausleihe, Beibehaltung des roten Farbschemas.
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from app_paths import resource_path_any


class FakeScanDialog(QDialog):
    """
    Demo-Dialog für den Scan-Vorgang (Jaclyn Barta).
    Simuliert die Kamera-Erkennung für die Sprint-Präsentation.
    """

    def __init__(self, parent=None, title="QR scannen", items=None, color="#E57368"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(700, 520)
        self.setStyleSheet("background:#FFFFFF;")

        self.result_text = None
        self._color = color
        self._items = items or []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.lbl_info = QLabel("📷 Kamera aktiv… Halte den QR-Code vor die Kamera.")
        self.lbl_info.setFont(QFont("Open Sans", 12, QFont.Weight.Bold))
        self.lbl_info.setStyleSheet("color:#333333;")
        layout.addWidget(self.lbl_info)

        self.video_placeholder = QLabel("LIVE-KAMERA (Simuliert)")
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setMinimumSize(640, 360)
        self.video_placeholder.setStyleSheet(
            "border: 2px solid #E0E0E0; border-radius: 10px; background:#F9F9F9; color:#666666;"
        )
        layout.addWidget(self.video_placeholder)

        self.lbl_status = QLabel("Status: Warte auf Scan…")
        layout.addWidget(self.lbl_status)

        self.combo = QComboBox()
        self.combo.setStyleSheet("padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px;")
        self.combo.addItem("Bitte auswählen (Demo)…")
        for x in self._items:
            self.combo.addItem(x)
        layout.addWidget(self.combo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_demo_scan = QPushButton("Demo-Scan")

        self.btn_cancel.setStyleSheet(
            "background-color: #E0E0E0; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_demo_scan.setStyleSheet(
            f"background-color: {self._color}; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_demo_scan.clicked.connect(self._do_demo_scan)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_demo_scan)
        layout.addLayout(btn_row)

    def _do_demo_scan(self):
        picked = self.combo.currentText()
        if picked.startswith("Bitte auswählen"): return
        self.result_text = picked
        self.accept()


class RueckgabeWidget(QWidget):
    COLOR_RED = "#E57368"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Dummy-Daten für die Demo (Simulation EPIC 7)
        self.dummy_loans = {
            "101": [
                {"isbn": "9783123456789", "titel": "Mathe 5", "status": "Ausgeliehen"},
                {"isbn": "9783120000001", "titel": "Deutsch 6", "status": "Ausgeliehen"}
            ],
            "102": [
                {"isbn": "9783129999999", "titel": "Englisch 7", "status": "Ausgeliehen"}
            ]
        }
        self.current_student_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
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
        header_layout.addWidget(logo_label)
        main_layout.addLayout(header_layout)

        main_layout.addWidget(QLabel("Startseite > Hauptmenü > Rückgabe"))

        page_title = QLabel("Rückgabe")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {self.COLOR_RED};")
        main_layout.addWidget(page_title)

        # --- SCAN BEREICH ---
        scan_area = QHBoxLayout()
        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Erst Schüler scannen...")
        self.in_student.setReadOnly(True)
        self.in_student.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background: #F3F3F3;")

        self.btn_scan_student = QPushButton("Schüler scannen")
        self.btn_scan_student.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_student.clicked.connect(self.scan_student)

        scan_area.addWidget(self.in_student)
        scan_area.addWidget(self.btn_scan_student)
        main_layout.addLayout(scan_area)

        # --- TABELLE ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ISBN", "Titel", "Status"])
        self.table.setStyleSheet(
            f"QHeaderView::section {{ background-color: #F0F0F0; border-bottom: 3px solid {self.COLOR_RED}; font-weight: bold; }}")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        # --- AKTIONEN ---
        actions_layout = QHBoxLayout()
        self.btn_next_student = QPushButton("Nächster Schüler")
        self.btn_next_student.setStyleSheet(
            "background-color: #E0E0E0; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_next_student.clicked.connect(self.reset_view)

        self.btn_scan_book = QPushButton("Buch scannen (Rückgabe)")
        self.btn_scan_book.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;")
        self.btn_scan_book.setEnabled(False)
        self.btn_scan_book.clicked.connect(self.scan_book_return)

        actions_layout.addWidget(self.btn_next_student)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_scan_book)
        main_layout.addLayout(actions_layout)

        # --- FOOTER ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.zurueck_btn = QPushButton("⬅ Zurück zum Hauptmenü")
        self.zurueck_btn.setStyleSheet(
            f"background-color: {self.COLOR_RED}; color: white; padding: 10px 25px; font-weight: bold; border-radius: 6px;")
        footer_layout.addWidget(self.zurueck_btn)
        main_layout.addLayout(footer_layout)

    def scan_student(self):
        items = ["101 - Max Müller", "102 - Lisa Schmidt"]
        d = FakeScanDialog(self, title="Schüler QR scannen", items=items, color=self.COLOR_RED)
        if d.exec() == QDialog.DialogCode.Accepted:
            picked = d.result_text
            self.in_student.setText(picked)
            self.current_student_id = picked.split(" - ")[0]
            self.load_student_books()

    def load_student_books(self):
        """Lädt die Liste der ausgeliehenen Bücher (Jaclyn Barta)"""
        books = self.dummy_loans.get(self.current_student_id, [])
        if not books:
            QMessageBox.critical(self, "Fehler", "Liste konnte nicht geladen werden.")
            return

        self.table.setRowCount(len(books))
        for row, book in enumerate(books):
            self.table.setItem(row, 0, QTableWidgetItem(book["isbn"]))
            self.table.setItem(row, 1, QTableWidgetItem(book["titel"]))
            self.table.setItem(row, 2, QTableWidgetItem(book["status"]))

        self.btn_scan_book.setEnabled(True)

    def scan_book_return(self):
        """Buch-Scan Rückgabe-Logik (Jaclyn Barta)"""
        if not self.current_student_id: return

        books_in_list = [self.table.item(r, 0).text() for r in range(self.table.rowCount())]
        d = FakeScanDialog(self, title="Buch-Scan Rückgabe", items=books_in_list, color=self.COLOR_RED)

        if d.exec() == QDialog.DialogCode.Accepted:
            scanned_isbn = d.result_text
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).text() == scanned_isbn:
                    status_item = QTableWidgetItem("✅ Zurückgegeben")
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, 2, status_item)
                    QMessageBox.information(self, "Erfolg", f"Buch {scanned_isbn} erfolgreich zurückgegeben.")
                    break

    def reset_view(self):
        """Setzt die Ansicht für den nächsten Schüler zurück (Jaclyn Barta)"""
        self.in_student.clear()
        self.table.setRowCount(0)
        self.btn_scan_book.setEnabled(False)
        self.current_student_id = None
