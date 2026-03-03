# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: AusleiheWidget (GUI Design & Sprint-Demo Scan ohne OpenCV)
# Datei: Ausleihe.py
#
# Autoren: Batuhan Aktürk & Daniel Popp (Entstanden im Pair Programming)
#
# - Daniel Popp: Haupt-GUI Architektur, Layout-Design, Tabellen-Aufbau & Styling,
#                Basis-Widget-Logik, Darkmode-Fix (show_message).
# - Batuhan Aktürk: Dialog-Klassen (LoanItemDialog, FakeScanDialog),
#                   Timer-Logik für Fake-Scan, Eingabe-Validierung, Daten-Management.
#
# Stand:
# - Schüler & Buch nur per "Scan" erfassen (Demo-Scan, ohne OpenCV)
# - UI sieht so aus, als ob Kamera scannt (Eingabefelder sind read-only)
# - Tabelle zeigt: welcher Schüler welches Buch ausleiht (Kontrolle vor Speichern)
# - Aktionen: Bearbeiten + Löschen
#
# Hinweis für den nächsten Sprint:
# - Der `FakeScanDialog` kann später nahtlos durch eine echte OpenCV-Kamera
#   ersetzt werden. Die Dummy-Listen können durch SQLite-Queries ersetzt werden.
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap


# ==============================================================================
# [Autor: Batuhan Aktürk]
# Dialog: Ausleihe-Eintrag bearbeiten
# Zweck: Gibt dem Nutzer die Möglichkeit, eingescannte Daten vor dem
#        Speichern manuell zu korrigieren (z.B. falls Auflage fehlt).
# ==============================================================================
class LoanItemDialog(QDialog):
    def __init__(self, parent=None, item=None, color="#8DBF42"):
        super().__init__(parent)
        self.setWindowTitle("Ausleihe bearbeiten")
        self.setFixedSize(450, 360)

        # Basis-Styling für den Dialog erzwingen
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #333333; font-weight: bold; }
            QLineEdit { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 6px; color: #333333; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #8DBF42; }
        """)
        self._color = color

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(14)

        # Eingabefelder definieren
        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("z.B. 101 - Max Mustermann (10A)")
        self.in_isbn = QLineEdit()
        self.in_isbn.setPlaceholderText("ISBN")
        self.in_title = QLineEdit()
        self.in_title.setPlaceholderText("Titel")
        self.in_publisher = QLineEdit()
        self.in_publisher.setPlaceholderText("Verlag")
        self.in_edition = QLineEdit()
        self.in_edition.setPlaceholderText("Auflage")

        # Falls ein Item übergeben wurde, Felder vorbefüllen
        if item:
            self.in_student.setText(item.get("student_display", ""))
            self.in_isbn.setText(item.get("isbn", ""))
            self.in_title.setText(item.get("titel", ""))
            self.in_publisher.setText(item.get("verlag", ""))
            self.in_edition.setText(item.get("auflage", ""))

        # Fehler-Label (Versteckt bis Validation fehlschlägt)
        self.error_label = QLabel("Bitte Pflichtfelder ausfüllen (Schüler, ISBN, Titel).")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic; font-weight: normal;")
        self.error_label.hide()

        form.addRow(QLabel("Schüler*:"), self.in_student)
        form.addRow(QLabel("ISBN*:"), self.in_isbn)
        form.addRow(QLabel("Titel*:"), self.in_title)
        form.addRow(QLabel("Verlag:"), self.in_publisher)
        form.addRow(QLabel("Auflage:"), self.in_edition)

        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")

        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 7px 17px; border: 3px solid #E0E0E0; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; color: white; }
        """)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{ background-color: {self._color}; color: white; padding: 7px 17px; border: 3px solid {self._color}; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
            QPushButton:pressed {{ background-color: #444444; border: 3px solid #444444; }}
        """)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._validate)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

    def _validate(self):
        """[Autor: Batuhan Aktürk] Prüft, ob alle Pflichtfelder ausgefüllt sind."""
        s = self.in_student.text().strip()
        isbn = self.in_isbn.text().strip()
        t = self.in_title.text().strip()

        # Reset Styles
        self.in_student.setStyleSheet("")
        self.in_isbn.setStyleSheet("")
        self.in_title.setStyleSheet("")

        ok = True
        if not s:
            self.in_student.setStyleSheet("border: 2px solid #D32F2F;")
            ok = False
        if not isbn:
            self.in_isbn.setStyleSheet("border: 2px solid #D32F2F;")
            ok = False
        if not t:
            self.in_title.setStyleSheet("border: 2px solid #D32F2F;")
            ok = False

        if not ok:
            self.error_label.show()
            return

        self.accept()  # Schließt Dialog mit "Erfolg"


# ==============================================================================
# [Autor: Batuhan Aktürk]
# Demo-Dialog: "Kamera Scan" (Fake)
# Zweck: Simuliert für die Sprint-Demo den Scanvorgang, damit das Programm
#        ohne fertige OpenCV-Implementierung getestet und vorgeführt werden kann.
# ==============================================================================
class FakeScanDialog(QDialog):
    def __init__(self, parent=None, title="QR scannen", label="Auswahl", items=None, color="#8DBF42"):
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

        # "Video"-Placeholder (Hier kommt später das cv2 Video-Label hin)
        self.video_placeholder = QLabel(
            "LIVE-KAMERA (Demo)\n\n[Hier wird im nächsten Sprint\nder OpenCV-Stream angezeigt]")
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setMinimumSize(640, 360)
        self.video_placeholder.setStyleSheet(
            "border: 2px solid #E0E0E0; border-radius: 10px; background:#F9F9F9; color:#666666; font-size: 14px;"
        )
        layout.addWidget(self.video_placeholder)

        self.lbl_status = QLabel("Status: Scanne…")
        self.lbl_status.setStyleSheet("color:#666666;")
        layout.addWidget(self.lbl_status)

        # Dropdown Auswahl für deterministische Tests
        self.combo = QComboBox()
        self.combo.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        )
        self.combo.addItem("Bitte auswählen (Demo)…")
        for x in self._items:
            self.combo.addItem(x)
        layout.addWidget(self.combo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_demo_scan = QPushButton("Demo-Scan")

        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 10px 20px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
        """)
        self.btn_demo_scan.setStyleSheet(f"""
            QPushButton {{ background-color: {self._color}; color: white; padding: 10px 20px; border: 3px solid {self._color}; border-radius: 6px; font-weight: bold; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_demo_scan.clicked.connect(self._do_demo_scan)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_demo_scan)
        layout.addLayout(btn_row)

        # Fake Scan Animation via Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._tick_state = 0
        self._timer.start(450)

    def _tick(self):
        """[Autor: Batuhan Aktürk] Ändert den Status-Text für die Illusion eines aktiven Scans."""
        self._tick_state += 1
        if self._tick_state % 3 == 1:
            self.lbl_status.setText("Status: Kamera fokussiert…")
        elif self._tick_state % 3 == 2:
            self.lbl_status.setText("Status: QR wird erkannt…")
        else:
            self.lbl_status.setText("Status: Scanne…")

    def _show_message(self, title, text):
        """Lokaler Darkmode-Fix für Popups im Dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #333333; font-size: 14px; }
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 6px 15px; border-radius: 4px; border: 1px solid #CCCCCC; font-weight: bold; }
        """)
        msg.exec()

    def _do_demo_scan(self):
        """Beendet den Demo-Scan und liefert den Wert zurück."""
        picked = self.combo.currentText()
        if picked.startswith("Bitte auswählen"):
            self._show_message("Hinweis", "Bitte im Dropdown einen Demo-QR auswählen.")
            return

        self.lbl_status.setText(f"Status: QR erkannt: {picked}")
        self.result_text = picked
        self._timer.stop()

        # Leichte Verzögerung für realistische UX
        QTimer.singleShot(400, self.accept)

    def closeEvent(self, event):
        try:
            if self._timer.isActive():
                self._timer.stop()
        except Exception:
            pass
        super().closeEvent(event)


# ==============================================================================
# [Autor: Daniel Popp]
# Haupt-Widget: AusleiheWidget
# Zweck: Das Kernmodul für die Ausleihe. Beinhaltet das UI-Layout, die Tabelle
#        und verknüpft die Scan-Dialoge mit der Geschäftslogik.
# ==============================================================================
class AusleiheWidget(QWidget):
    COLOR = "#8DBF42"  # Ausleihe Farbe (wie im Hauptmenü)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Zustand des aktuellen Ausleih-Vorgangs
        self.current_student = None
        self.loan_items = []

        # Dummy-Daten (Werden in zukünftigen Sprints durch SQLite ersetzt)
        self.dummy_students = [
            {"id": "101", "name": "Max Müller", "klasse": "10A"},
            {"id": "102", "name": "Lisa Schmidt", "klasse": "10A"},
            {"id": "201", "name": "Ali Yilmaz", "klasse": "11B"},
        ]
        self.dummy_books = [
            {"isbn": "9783123456789", "titel": "Mathe 5", "verlag": "Cornelsen", "auflage": "2023"},
            {"isbn": "9783120000001", "titel": "Deutsch 6", "verlag": "Klett", "auflage": "2022"},
            {"isbn": "9783129999999", "titel": "Englisch 7", "verlag": "Klett", "auflage": "2021"},
        ]

        # ---------------- Layout [Autor: Daniel Popp] ----------------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

        # ================= HEADER =================
        header_layout = QHBoxLayout()

        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = self.get_image_path("technikerschule_logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)

        # ================= BREADCRUMBS =================
        self.back_label = QLabel("Startseite > Hauptmenü > Ausleihe")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        # ================= TITEL =================
        page_title = QLabel("Ausleihe")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {self.COLOR}; margin-left: 10px;")
        main_layout.addWidget(page_title)

        hint = QLabel("Erfassung nur per QR-Scan (Demo): Schüler scannen → Buch scannen → Tabelle prüfen → speichern.")
        hint.setStyleSheet("color: #333333; margin-left: 10px;")
        main_layout.addWidget(hint)

        # ================= SCHÜLER-BEREICH =================
        student_area = QHBoxLayout()
        student_area.setContentsMargins(10, 10, 10, 5)
        student_area.setSpacing(15)

        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Schüler-QR wird hier angezeigt (Scan erforderlich)")
        self.in_student.setFixedWidth(520)
        self.in_student.setReadOnly(True)  # Verhindert manuelle Eingabe
        self.in_student.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.in_student.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #F3F3F3; color: #333333; font-size: 14px;"
        )
        student_area.addWidget(self.in_student)

        self.btn_scan_student = QPushButton("Schüler scannen")
        self.btn_scan_student.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 10px 25px; border: 3px solid {self.COLOR}; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)
        self.btn_scan_student.clicked.connect(self.scan_student)
        student_area.addWidget(self.btn_scan_student)

        student_area.addStretch()
        main_layout.addLayout(student_area)

        self.lbl_student_status = QLabel("Kein Schüler ausgewählt.")
        self.lbl_student_status.setStyleSheet("color: #666666; margin-left: 10px;")
        main_layout.addWidget(self.lbl_student_status)

        # ================= BUCH-BEREICH =================
        book_area = QHBoxLayout()
        book_area.setContentsMargins(10, 10, 10, 5)
        book_area.setSpacing(15)

        self.in_book = QLineEdit()
        self.in_book.setPlaceholderText("Buch-QR wird hier angezeigt (Scan erforderlich)")
        self.in_book.setFixedWidth(520)
        self.in_book.setReadOnly(True)
        self.in_book.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.in_book.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #F3F3F3; color: #333333; font-size: 14px;"
        )
        book_area.addWidget(self.in_book)

        self.btn_scan_book = QPushButton("Buch scannen")
        self.btn_scan_book.setStyleSheet("""
            QPushButton { background-color: #8DBF42; color: #FFFFFF; padding: 10px 25px; border: 3px solid #8DBF42; border-radius: 6px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { border: 3px solid #333333; }
        """)
        self.btn_scan_book.clicked.connect(self.scan_book)
        self.btn_scan_book.setEnabled(False)  # Erst aktiv, wenn Schüler gewählt wurde
        book_area.addWidget(self.btn_scan_book)

        book_area.addStretch()
        main_layout.addLayout(book_area)

        # ================= TABELLE [Autor: Daniel Popp] =================
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Schüler", "ISBN", "Titel", "Verlag", "Auflage", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF; alternate-background-color: #F9F9F9; border: 1px solid #E0E0E0;
                border-radius: 8px; gridline-color: #EDEDED; font-size: 15px; color: #333333;
            }}
            QHeaderView::section {{
                background-color: #F0F0F0; color: #000000; font-weight: bold;
                border: none; border-bottom: 3px solid {self.COLOR}; padding: 12px;
            }}
        """)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Schüler
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # ISBN
        self.table.setColumnWidth(1, 170)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Titel
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Verlag
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Auflage
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Aktionen
        self.table.setColumnWidth(5, 160)

        main_layout.addWidget(self.table)

        # ================= BUTTONS UNTER TABELLE =================
        bottom_actions = QHBoxLayout()
        bottom_actions.setContentsMargins(10, 0, 10, 0)

        self.btn_finish = QPushButton("Ausleihe abschließen")
        self.btn_finish.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 12px 25px; border: 3px solid {self.COLOR}; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)
        self.btn_finish.clicked.connect(self.finish_loan)
        self.btn_finish.setEnabled(False)
        bottom_actions.addWidget(self.btn_finish)

        bottom_actions.addStretch()

        self.btn_reset = QPushButton("Zurücksetzen")
        self.btn_reset.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 12px 25px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { border: 3px solid #333333; }
        """)
        self.btn_reset.clicked.connect(self.reset_all)
        self.btn_reset.setEnabled(False)
        bottom_actions.addWidget(self.btn_reset)

        main_layout.addLayout(bottom_actions)

        # ================= FOOTER =================
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        # Wichtig: MainWindow verbindet diesen Button -> zurück ins Hauptmenü
        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 12px 25px; border: 3px solid {self.COLOR}; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    # ---------------- Helper ----------------
    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    def show_message(self, title, text):
        """[Autor: Daniel Popp] Behebt den MacOS/Windows Darkmode-Bug (weiße Schrift auf weißem Grund)."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #333333; font-size: 14px; }
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 6px 15px; border-radius: 4px; border: 1px solid #CCCCCC; font-weight: bold; }
            QPushButton:hover { background-color: #D0D0D0; }
        """)
        msg.exec()

    # ==============================================================================
    # [Autor: Batuhan Aktürk & Daniel Popp]
    # Logik: Schüler-Scan verarbeiten
    # ==============================================================================
    def scan_student(self):
        items = [f"{s['id']} - {s['name']} ({s['klasse']})" for s in self.dummy_students]
        d = FakeScanDialog(self, title="Schüler QR scannen (Demo)", label="Schüler auswählen:", items=items,
                           color=self.COLOR)

        if d.exec() != QDialog.DialogCode.Accepted or not d.result_text:
            return

        picked = d.result_text
        self.in_student.setText(picked)

        # Schüler-ID extrahieren und in Dummy-Liste suchen
        sid = picked.split(" - ")[0].strip()
        s = next((x for x in self.dummy_students if x["id"] == sid), None)
        self.current_student = s if s else {"id": sid, "name": "Unbekannt", "klasse": "—"}

        display = f"{self.current_student['id']} - {self.current_student['name']} ({self.current_student['klasse']})"
        self.lbl_student_status.setText(f"Schüler ausgewählt: {display}")
        self.lbl_student_status.setStyleSheet("color: #333333; margin-left: 10px; font-weight: bold;")

        # UI-Elemente für den nächsten Schritt freischalten
        self.btn_scan_book.setEnabled(True)
        self.btn_finish.setEnabled(True)
        self.btn_reset.setEnabled(True)

    # ==============================================================================
    # [Autor: Batuhan Aktürk & Daniel Popp]
    # Logik: Buch-Scan verarbeiten
    # ==============================================================================
    def scan_book(self):
        if not self.current_student:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler scannen.")
            return

        items = [f"{b['isbn']} - {b['titel']} ({b['verlag']}, {b['auflage']})" for b in self.dummy_books]
        d = FakeScanDialog(self, title="Buch QR scannen (Demo)", label="Buch auswählen:", items=items, color=self.COLOR)

        if d.exec() != QDialog.DialogCode.Accepted or not d.result_text:
            return

        picked = d.result_text
        self.in_book.setText(picked)

        # ISBN extrahieren und in Dummy-Liste suchen
        isbn = picked.split(" - ")[0].strip()
        b = next((x for x in self.dummy_books if x["isbn"] == isbn), None)
        if not b:
            b = {"isbn": isbn, "titel": "Unbekanntes Buch", "verlag": "—", "auflage": "—"}

        student_display = f"{self.current_student['id']} - {self.current_student['name']} ({self.current_student['klasse']})"

        # Doppelte Scans verhindern (selber Schüler, selbes Buch)
        if any(x["student_id"] == self.current_student["id"] and x["isbn"] == isbn for x in self.loan_items):
            self.show_message("Hinweis", "Dieses Buch ist für diesen Schüler bereits in der Liste.")
            return

        # Zur Liste hinzufügen und Tabelle neu laden
        self.loan_items.append({
            "student_id": self.current_student["id"],
            "student_display": student_display,
            "isbn": b["isbn"],
            "titel": b["titel"],
            "verlag": b["verlag"],
            "auflage": b["auflage"],
        })
        self.reload_table()

    # ==============================================================================
    # [Autor: Daniel Popp]
    # Logik: Tabelle befüllen und updaten
    # ==============================================================================
    def reload_table(self):
        self.table.setRowCount(len(self.loan_items))

        for row, item in enumerate(self.loan_items):
            # Zellen befüllen und auf 'ReadOnly' setzen
            it_s = QTableWidgetItem(item["student_display"])
            it_s.setFlags(it_s.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, it_s)

            it_isbn = QTableWidgetItem(item["isbn"])
            it_isbn.setFlags(it_isbn.flags() ^ Qt.ItemFlag.ItemIsEditable)
            it_isbn.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, it_isbn)

            it_t = QTableWidgetItem(item["titel"])
            it_t.setFlags(it_t.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, it_t)

            it_v = QTableWidgetItem(item["verlag"])
            it_v.setFlags(it_v.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, it_v)

            it_a = QTableWidgetItem(item["auflage"])
            it_a.setFlags(it_a.flags() ^ Qt.ItemFlag.ItemIsEditable)
            it_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, it_a)

            self._set_actions_widget(row)

    def _set_actions_widget(self, row):
        """Generiert die Buttons für die Spalte 'Aktionen' pro Zeile."""
        bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

        action_widget = QWidget()
        action_widget.setStyleSheet(f"background-color: {bg_color};")

        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 0, 5, 0)
        action_layout.setSpacing(15)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bearbeiten-Button
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(45, 45)
        btn_edit.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { background-color: #E0E0E0; border-radius: 8px; }"
        )
        # Lambda bindet die aktuelle row, um beim Klick den richtigen Index zu haben
        btn_edit.clicked.connect(lambda ch, r=row: self.edit_item(r))

        # Löschen-Button
        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(45, 45)
        btn_delete.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { background-color: #FFCDD2; border-radius: 8px; }"
        )
        btn_delete.clicked.connect(lambda ch, r=row: self.remove_item(r))

        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, action_widget)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Bearbeiten und Löschen von Tabelleneinträgen
    # ==============================================================================
    def edit_item(self, row_index):
        """Öffnet den Bearbeitungs-Dialog für die ausgewählte Tabellenzeile."""
        if row_index < 0 or row_index >= len(self.loan_items):
            return

        item = self.loan_items[row_index]
        d = LoanItemDialog(self, item=item, color=self.COLOR)

        # Wenn Speichern geklickt wurde, Werte übernehmen und Tabelle updaten
        if d.exec() == QDialog.DialogCode.Accepted:
            self.loan_items[row_index]["student_display"] = d.in_student.text().strip()
            self.loan_items[row_index]["isbn"] = d.in_isbn.text().strip()
            self.loan_items[row_index]["titel"] = d.in_title.text().strip()
            self.loan_items[row_index]["verlag"] = d.in_publisher.text().strip()
            self.loan_items[row_index]["auflage"] = d.in_edition.text().strip()
            self.reload_table()

    def remove_item(self, row_index):
        """Entfernt ein Element aus der Liste und aktualisiert die UI."""
        if row_index < 0 or row_index >= len(self.loan_items):
            return
        self.loan_items.pop(row_index)
        self.reload_table()

    # ==============================================================================
    # [Autor: Daniel Popp & Batuhan Aktürk]
    # Logik: Abschluss / Reset
    # ==============================================================================
    def reset_all(self):
        """Setzt die komplette Ausleihe-Ansicht auf den Startzustand zurück."""
        self.current_student = None
        self.loan_items = []

        self.in_student.clear()
        self.in_book.clear()

        # Buttons wieder sperren
        self.btn_scan_book.setEnabled(False)
        self.btn_finish.setEnabled(False)
        self.btn_reset.setEnabled(False)

        self.lbl_student_status.setText("Kein Schüler ausgewählt.")
        self.lbl_student_status.setStyleSheet("color: #666666; margin-left: 10px;")

        self.reload_table()

    def finish_loan(self):
        """Validiert die Liste und simuliert das Speichern der Daten in der DB."""
        if not self.loan_items:
            self.show_message("Hinweis", "Keine Ausleihe-Einträge vorhanden.")
            return

        self.show_message(
            "Ausleihe abgeschlossen",
            f"Ausleihe gespeichert!\n\nEinträge gesamt: {len(self.loan_items)}"
        )
        self.reset_all()