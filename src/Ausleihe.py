# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: AusleiheWidget (GUI Design & Sprint-Demo)
# Datei: Ausleihe.py
#
# Autoren: Batuhan Aktürk & Daniel Popp (Entstanden im Pair Programming)
#
# Aufgabenverteilung / Änderungen in dieser Version:
#
# - Daniel Popp:
#   - Überarbeitung und Erweiterung des GUI-Layouts im Haupt-Widget
#   - Anpassung der Benutzeroberfläche für manuellen Fallback
#     (Schüler-ID / ISBN eingeben zusätzlich zum Scan)
#   - Integration und Gestaltung der Historienanzeige
#     ("Bereits ausgeliehene Bücher")
#   - Anpassung der Tabellenstruktur und der Button-Bereiche
#   - Entfernen der Bearbeiten-Funktion aus der Aktionsspalte
#   - Pflege des einheitlichen Stylings und Darkmode-Fix für Popups
#
# - Batuhan Aktürk:
#   - Erweiterung der Logik für Schüler- und Bucherfassung
#     (Scan + manuelle Eingabe als gemeinsamer Workflow)
#   - Einführung der zentralen Verarbeitungsfunktionen
#     `_process_student()` und `_process_book()`
#   - Einbau der Dummy-Historie und Fehlerfall-Simulation
#     ("Liste konnte nicht geladen werden")
#   - Implementierung des Buttons "Nächster Schüler (Reset)"
#   - Anpassung der Zustandslogik für Freischalten/Sperren der UI-Elemente
#   - Pflege des FakeScanDialog inkl. Timer-Logik und Demo-Scan-Ablauf
#
# Stand (Epic 7):
# - Schüler & Buch per Scan ODER manueller Eingabe erfassen (Fallback)
# - Anzeige der "Bereits ausgeliehenen Bücher" nach Schüler-Erfassung
# - "Nächster Schüler" Button zum sauberen Zurücksetzen des Workflows
# - Fehlerfall-Simulation eingebaut (Liste konnte nicht geladen werden)
# - Editieren entfernt (nur noch Löschen möglich, strenger Workflow)
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap


# ==============================================================================
# [Autor: Batuhan Aktürk]
# Demo-Dialog: "Kamera Scan" (Fake)
# Zweck:
# - Simuliert für die Sprint-Demo den Scanvorgang
# - Ermöglicht Testbarkeit ohne fertige OpenCV-Implementierung
# - Wurde in dieser Version weiterverwendet und in den neuen Workflow
#   (Scan + manuelle Eingabe) eingebunden
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

        # Platzhalter für den späteren echten Kamera-Stream
        self.video_placeholder = QLabel(
            "LIVE-KAMERA (Demo)\n\n[Hier wird im nächsten Sprint\nder OpenCV-Stream angezeigt]"
        )
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setMinimumSize(640, 360)
        self.video_placeholder.setStyleSheet(
            "border: 2px solid #E0E0E0; border-radius: 10px; background:#F9F9F9; color:#666666; font-size: 14px;"
        )
        layout.addWidget(self.video_placeholder)

        self.lbl_status = QLabel("Status: Scanne…")
        self.lbl_status.setStyleSheet("color:#666666;")
        layout.addWidget(self.lbl_status)

        # Dropdown für kontrollierte Demo-Auswahl
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

        # [Autor: Batuhan Aktürk]
        # Fake-Animation per Timer für realistischeren Demo-Effekt
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._tick_state = 0
        self._timer.start(450)

    def _tick(self):
        """[Autor: Batuhan Aktürk] Wechselt die Statusanzeige zyklisch für die Demo."""
        self._tick_state += 1
        if self._tick_state % 3 == 1:
            self.lbl_status.setText("Status: Kamera fokussiert…")
        elif self._tick_state % 3 == 2:
            self.lbl_status.setText("Status: QR wird erkannt…")
        else:
            self.lbl_status.setText("Status: Scanne…")

    def _show_message(self, title, text):
        """[Autor: Batuhan Aktürk] Lokaler Popup-Fix für gut lesbare Meldungen."""
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
        """[Autor: Batuhan Aktürk] Übernimmt die Demo-Auswahl und beendet den Dialog."""
        picked = self.combo.currentText()
        if picked.startswith("Bitte auswählen"):
            self._show_message("Hinweis", "Bitte im Dropdown einen Demo-QR auswählen.")
            return

        self.lbl_status.setText(f"Status: QR erkannt: {picked}")
        self.result_text = picked
        self._timer.stop()

        # Kleine Verzögerung für realistischeren Ablauf
        QTimer.singleShot(400, self.accept)

    def closeEvent(self, event):
        """[Autor: Batuhan Aktürk] Stoppt den Timer sauber beim Schließen des Dialogs."""
        try:
            if self._timer.isActive():
                self._timer.stop()
        except Exception:
            pass
        super().closeEvent(event)


# ==============================================================================
# [Autor: Daniel Popp & Batuhan Aktürk]
# Haupt-Widget: AusleiheWidget
#
# Daniel Popp:
# - GUI-Grundaufbau, Layout-Struktur, Styling, Tabellenaufbau,
#   Historienbereich und Button-Anordnung
#
# Batuhan Aktürk:
# - Workflow-Logik für Schüler- und Buchverarbeitung,
#   Freischaltung der Eingaben, Reset-Logik und Fehlerfall-Simulation
# ==============================================================================
class AusleiheWidget(QWidget):
    COLOR = "#8DBF42"
    ALT_COLOR = "#007BFF"  # derzeit vorbereitet, aber im aktuellen Stand nicht aktiv genutzt

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # [Autor: Batuhan Aktürk]
        # Zustand des aktuellen Ausleihvorgangs
        self.current_student = None
        self.loan_items = []

        # ----------------------------------------------------------------------
        # [Autor: Batuhan Aktürk]
        # DUMMY DATEN:
        # - Werden für Demo und Sprint-Präsentation verwendet
        # - Die Historie simuliert bereits ausgeliehene Bücher
        # - Für Schüler-ID "201" wird absichtlich ein Fehlerfall simuliert
        # ----------------------------------------------------------------------
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

        self.dummy_history = {
            "101": [{"isbn": "9783129999000", "titel": "Physik 10 (Ausgeliehen am 10.10.2025)"}],
            "102": [],
            "201": None
        }

        # ----------------------------------------------------------------------
        # [Autor: Daniel Popp]
        # Layout-Erweiterung:
        # - Manueller Fallback für Schüler- und Bucherfassung ergänzt
        # - Historienbereich unterhalb der Schülerauswahl eingebaut
        # - Button-Bereiche und Workflow visuell angepasst
        # ----------------------------------------------------------------------
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

        # ================= BREADCRUMBS & TITEL =================
        self.back_label = QLabel("Startseite > Hauptmenü > Ausleihe")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        page_title = QLabel("Ausleihe")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {self.COLOR}; margin-left: 10px;")
        main_layout.addWidget(page_title)

        hint = QLabel("Ablauf: Schüler scannen oder ID eingeben → Buch scannen/eingeben → Tabelle prüfen → speichern.")
        hint.setStyleSheet("color: #333333; margin-left: 10px;")
        main_layout.addWidget(hint)

        # ================= SCHÜLER-BEREICH =================
        # [Autor: Daniel Popp]
        # GUI-Anpassung:
        # - Schüler kann jetzt per Scan oder per manueller Eingabe übernommen werden
        # - Zusätzlicher Button "Übernehmen" als Fallback
        student_area = QHBoxLayout()
        student_area.setContentsMargins(10, 10, 10, 5)
        student_area.setSpacing(10)

        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Schüler-ID eingeben oder scannen...")
        self.in_student.setFixedWidth(400)
        self.in_student.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        )
        self.in_student.returnPressed.connect(self.manual_student_enter)
        student_area.addWidget(self.in_student)

        self.btn_manual_student = QPushButton("Übernehmen")
        self.btn_manual_student.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #75A036; }}
        """)
        self.btn_manual_student.clicked.connect(self.manual_student_enter)
        student_area.addWidget(self.btn_manual_student)

        self.btn_scan_student = QPushButton("Schülerausweis scannen")
        self.btn_scan_student.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #75A036; }}
        """)
        self.btn_scan_student.clicked.connect(self.scan_student)
        student_area.addWidget(self.btn_scan_student)

        student_area.addStretch()
        main_layout.addLayout(student_area)

        self.lbl_student_status = QLabel("Kein Schüler ausgewählt.")
        self.lbl_student_status.setStyleSheet("color: #666666; margin-left: 10px;")
        main_layout.addWidget(self.lbl_student_status)

        # ================= HISTORIE =================
        # [Autor: Daniel Popp]
        # Neuer UI-Bereich:
        # - Zeigt nach Schülerauswahl bereits ausgeliehene Bücher an
        # - Unterstützt einen transparenteren Ausleihprozess
        # - Bereich bleibt zunächst verborgen und wird erst später eingeblendet
        self.lbl_history = QLabel("Bereits ausgeliehene Bücher:")
        self.lbl_history.setStyleSheet("color: #333333; font-weight: bold; margin-left: 10px; margin-top: 10px;")
        self.lbl_history.hide()
        main_layout.addWidget(self.lbl_history)

        self.table_history = QTableWidget(0, 2)
        self.table_history.setHorizontalHeaderLabels(["ISBN", "Titel"])
        self.table_history.setMaximumHeight(100)
        self.table_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_history.setStyleSheet("""
            QTableWidget { background-color: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 6px; color: #333333; }
            QHeaderView::section { background-color: #E9ECEF; color: #495057; font-weight: bold; border: none; border-bottom: 2px solid #DEE2E6; padding: 6px; }
        """)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.hide()
        main_layout.addWidget(self.table_history)

        main_layout.addSpacing(10)

        # ================= BUCH-BEREICH =================
        # [Autor: Daniel Popp]
        # GUI-Erweiterung:
        # - ISBN kann jetzt ebenfalls manuell eingegeben werden
        # - Bereich bleibt gesperrt, bis ein Schüler erfolgreich verarbeitet wurde
        book_area = QHBoxLayout()
        book_area.setContentsMargins(10, 5, 10, 5)
        book_area.setSpacing(10)

        self.in_book = QLineEdit()
        self.in_book.setPlaceholderText("ISBN eingeben oder scannen...")
        self.in_book.setFixedWidth(400)
        self.in_book.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        )
        self.in_book.setEnabled(False)
        self.in_book.returnPressed.connect(self.manual_book_enter)
        book_area.addWidget(self.in_book)

        self.btn_manual_book = QPushButton("Hinzufügen")
        self.btn_manual_book.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #75A036; }}
            QPushButton:disabled {{ background-color: #CCCCCC; color: #888888; }}
        """)
        self.btn_manual_book.clicked.connect(self.manual_book_enter)
        self.btn_manual_book.setEnabled(False)
        book_area.addWidget(self.btn_manual_book)

        self.btn_scan_book = QPushButton("QR-Code scannen")
        self.btn_scan_book.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 10px 15px; border-radius: 6px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #75A036; }}
            QPushButton:disabled {{ background-color: #CCCCCC; color: #888888; }}
        """)
        self.btn_scan_book.clicked.connect(self.scan_book)
        self.btn_scan_book.setEnabled(False)
        book_area.addWidget(self.btn_scan_book)

        book_area.addStretch()
        main_layout.addLayout(book_area)

        # ================= TABELLE =================
        # [Autor: Daniel Popp]
        # Tabellenanpassung:
        # - Bearbeiten wurde aus der Aktionsspalte entfernt
        # - Übrig bleibt ein reduzierter, strenger Workflow mit Löschen-Funktion
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Schüler", "ISBN", "Titel", "Verlag", "Auflage", "Aktion"])
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 170)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 100)

        main_layout.addWidget(self.table)

        # ================= BUTTONS UNTER TABELLE =================
        # [Autor: Daniel Popp]
        # UI-Anpassung:
        # - "Zurücksetzen" wurde ersetzt durch "Nächster Schüler (Reset)"
        # - Dadurch ist der Ablauf für den Benutzer klarer strukturiert
        bottom_actions = QHBoxLayout()
        bottom_actions.setContentsMargins(10, 10, 10, 0)

        bottom_actions.addStretch()

        self.btn_next_student = QPushButton("✖ Nächster Schüler (Reset)")
        self.btn_next_student.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 12px 25px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { border: 3px solid #333333; }
        """)
        self.btn_next_student.clicked.connect(self.reset_all)
        self.btn_next_student.setEnabled(False)
        bottom_actions.addWidget(self.btn_next_student)

        self.btn_finish = QPushButton("✔ Ausleihe abschließen")
        self.btn_finish.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 12px 25px; border: 3px solid {self.COLOR}; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)
        self.btn_finish.clicked.connect(self.finish_loan)
        self.btn_finish.setEnabled(False)
        bottom_actions.addWidget(self.btn_finish)

        main_layout.addLayout(bottom_actions)

        # ================= FOOTER =================
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR}; color: white; padding: 12px 25px; border: 3px solid {self.COLOR}; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ border: 3px solid #333333; }}
        """)
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    # --------------------------------------------------------------------------
    # [Autor: Daniel Popp]
    # Hilfsfunktion: Bildpfad für Logos / Grafiken auflösen
    # --------------------------------------------------------------------------
    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    # --------------------------------------------------------------------------
    # [Autor: Daniel Popp]
    # Popup-Hilfsfunktion:
    # - Behebt Darstellungsprobleme bei Darkmode auf verschiedenen Systemen
    # --------------------------------------------------------------------------
    def show_message(self, title, text):
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
    # [Autor: Batuhan Aktürk]
    # Logik: Manuelle Schüler-Erfassung
    # Zweck:
    # - Fallback, falls kein Scan möglich ist
    # - Übergibt die eingegebene Schüler-ID an die zentrale Verarbeitungsfunktion
    # ==============================================================================
    def manual_student_enter(self):
        sid = self.in_student.text().strip()
        if sid:
            self._process_student(sid)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Schüler per Demo-Scan erfassen
    # Zweck:
    # - Öffnet den FakeScanDialog
    # - Übergibt die ausgewählte Schüler-ID an die zentrale Verarbeitungsfunktion
    # ==============================================================================
    def scan_student(self):
        items = [f"{s['id']} - {s['name']} ({s['klasse']})" for s in self.dummy_students]
        d = FakeScanDialog(
            self,
            title="Schüler QR scannen (Demo)",
            label="Schüler auswählen:",
            items=items,
            color=self.COLOR
        )

        if d.exec() == QDialog.DialogCode.Accepted and d.result_text:
            sid = d.result_text.split(" - ")[0].strip()
            self._process_student(sid)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Kernlogik: Schüler verarbeiten
    # Zweck:
    # - Vereinheitlicht Scan und manuelle Eingabe in einer Funktion
    # - Setzt den aktuellen Schüler
    # - Lädt die Historie bereits ausgeliehener Bücher
    # - Simuliert optional einen Fehlerfall für die Demo
    # - Schaltet danach den Buchbereich frei
    # ==============================================================================
    def _process_student(self, sid):
        s = next((x for x in self.dummy_students if x["id"] == sid), None)
        self.current_student = s if s else {"id": sid, "name": "Unbekannt", "klasse": "—"}

        display = f"{self.current_student['id']} - {self.current_student['name']} ({self.current_student['klasse']})"
        self.lbl_student_status.setText(f"✅ Schüler ausgewählt: {display}")
        self.lbl_student_status.setStyleSheet("color: #333333; margin-left: 10px; font-weight: bold;")

        # [Autor: Batuhan Aktürk]
        # Eingabefeld wird vereinheitlicht, egal ob Scan oder manuelle Eingabe
        self.in_student.setText(display)

        # [Autor: Batuhan Aktürk]
        # Historie laden und in der Zusatz-Tabelle anzeigen
        history = self.dummy_history.get(sid, [])
        if history is None:
            self.show_message("Fehler", "Liste konnte nicht geladen werden.")
            self.table_history.setRowCount(0)
            self.lbl_history.setText(
                f"Fehler: Historie für {self.current_student['name']} konnte nicht geladen werden."
            )
            self.lbl_history.setStyleSheet("color: #D32F2F; font-weight: bold; margin-left: 10px;")
        else:
            self.lbl_history.setText(f"Bereits ausgeliehene Bücher von {self.current_student['name']}:")
            self.lbl_history.setStyleSheet("color: #333333; font-weight: bold; margin-left: 10px;")
            self.table_history.setRowCount(len(history))
            for i, item in enumerate(history):
                self.table_history.setItem(i, 0, QTableWidgetItem(item["isbn"]))
                self.table_history.setItem(i, 1, QTableWidgetItem(item["titel"]))

        self.lbl_history.show()
        self.table_history.show()

        # [Autor: Batuhan Aktürk]
        # Nach erfolgreicher Schülerverarbeitung wird der Buchbereich freigeschaltet
        self.in_book.setEnabled(True)
        self.btn_manual_book.setEnabled(True)
        self.btn_scan_book.setEnabled(True)
        self.btn_finish.setEnabled(True)
        self.btn_next_student.setEnabled(True)

        # Komfortfunktion: Fokus direkt auf das nächste Eingabefeld
        self.in_book.setFocus()

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Manuelle Buch-Erfassung
    # Zweck:
    # - Fallback für ISBN-Eingabe ohne Scan
    # - Übergibt die ISBN an die zentrale Buch-Verarbeitung
    # ==============================================================================
    def manual_book_enter(self):
        isbn = self.in_book.text().strip()
        if isbn:
            self._process_book(isbn)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Buch per Demo-Scan erfassen
    # Zweck:
    # - Öffnet den FakeScanDialog für Buchdaten
    # - Übergibt die erkannte ISBN an die zentrale Buch-Verarbeitung
    # ==============================================================================
    def scan_book(self):
        if not self.current_student:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler scannen oder eingeben.")
            return

        items = [f"{b['isbn']} - {b['titel']} ({b['verlag']}, {b['auflage']})" for b in self.dummy_books]
        d = FakeScanDialog(
            self,
            title="Buch QR scannen (Demo)",
            label="Buch auswählen:",
            items=items,
            color=self.COLOR
        )

        if d.exec() == QDialog.DialogCode.Accepted and d.result_text:
            isbn = d.result_text.split(" - ")[0].strip()
            self._process_book(isbn)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Kernlogik: Buch verarbeiten
    # Zweck:
    # - Vereinheitlicht Scan und manuelle Eingabe in einer Funktion
    # - Prüft auf doppelte Einträge
    # - Fügt das Buch zur aktuellen Ausleihliste hinzu
    # - Leert danach das Eingabefeld für den nächsten Vorgang
    # ==============================================================================
    def _process_book(self, isbn):
        if not self.current_student:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler auswählen.")
            return

        b = next((x for x in self.dummy_books if x["isbn"] == isbn), None)
        if not b:
            b = {"isbn": isbn, "titel": "Unbekanntes Buch", "verlag": "—", "auflage": "—"}

        student_display = f"{self.current_student['id']} - {self.current_student['name']} ({self.current_student['klasse']})"

        # [Autor: Batuhan Aktürk]
        # Verhindert doppelte Buchauswahl für denselben Schüler
        if any(x["student_id"] == self.current_student["id"] and x["isbn"] == isbn for x in self.loan_items):
            self.show_message("Hinweis", "Dieses Buch ist für diesen Schüler bereits in der Liste.")
            self.in_book.clear()
            self.in_book.setFocus()
            return

        self.loan_items.append({
            "student_id": self.current_student["id"],
            "student_display": student_display,
            "isbn": b["isbn"],
            "titel": b["titel"],
            "verlag": b["verlag"],
            "auflage": b["auflage"],
        })
        self.reload_table()

        # Nach erfolgreichem Hinzufügen direkt bereit für das nächste Buch
        self.in_book.clear()
        self.in_book.setFocus()

    # ==============================================================================
    # [Autor: Daniel Popp]
    # Logik: Tabelle neu aufbauen
    # Zweck:
    # - Lädt alle aktuellen Ausleiheinträge in die Tabelle
    # - Setzt Zellen auf nicht editierbar
    # - Verknüpft pro Zeile die Aktionsspalte
    # ==============================================================================
    def reload_table(self):
        self.table.setRowCount(len(self.loan_items))

        for row, item in enumerate(self.loan_items):
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

    # ==============================================================================
    # [Autor: Daniel Popp]
    # Logik: Aktionsspalte erzeugen
    # Zweck:
    # - Erstellt pro Tabellenzeile die Bedienelemente
    # - In dieser Version bewusst nur noch mit Löschen-Button
    # - Editieren wurde aus dem Workflow entfernt
    # ==============================================================================
    def _set_actions_widget(self, row):
        bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

        action_widget = QWidget()
        action_widget.setStyleSheet(f"background-color: {bg_color};")

        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 0, 5, 0)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(45, 45)
        btn_delete.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { background-color: #FFCDD2; border-radius: 8px; }"
        )
        btn_delete.clicked.connect(lambda ch, r=row: self.remove_item(r))

        action_layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, action_widget)

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Eintrag aus der aktuellen Ausleihliste entfernen
    # Zweck:
    # - Löscht einen ausgewählten Datensatz aus der Liste
    # - Baut die Tabelle anschließend neu auf
    # ==============================================================================
    def remove_item(self, row_index):
        if row_index < 0 or row_index >= len(self.loan_items):
            return
        self.loan_items.pop(row_index)
        self.reload_table()

    # ==============================================================================
    # [Autor: Batuhan Aktürk & Daniel Popp]
    # Logik: Workflow vollständig zurücksetzen
    #
    # Batuhan Aktürk:
    # - Zustandslogik zurücksetzen
    # - Eingaben leeren, Buttons sperren, Fokus neu setzen
    #
    # Daniel Popp:
    # - Historienbereich und Tabellenansicht visuell in den Startzustand zurückführen
    # ==============================================================================
    def reset_all(self):
        self.current_student = None
        self.loan_items = []

        self.in_student.clear()
        self.in_book.clear()

        self.table_history.setRowCount(0)
        self.table_history.hide()
        self.lbl_history.hide()

        # [Autor: Batuhan Aktürk]
        # Sperren bis ein neuer Schüler übernommen wird
        self.in_book.setEnabled(False)
        self.btn_manual_book.setEnabled(False)
        self.btn_scan_book.setEnabled(False)
        self.btn_finish.setEnabled(False)
        self.btn_next_student.setEnabled(False)

        self.lbl_student_status.setText("Kein Schüler ausgewählt.")
        self.lbl_student_status.setStyleSheet("color: #666666; margin-left: 10px;")

        self.reload_table()

        # Startfokus wieder auf Schüler-Eingabe
        self.in_student.setFocus()

    # ==============================================================================
    # [Autor: Batuhan Aktürk]
    # Logik: Ausleihe abschließen
    # Zweck:
    # - Prüft, ob Einträge vorhanden sind
    # - Simuliert das Speichern der Ausleihe
    # - Setzt danach den kompletten Workflow zurück
    # ==============================================================================
    def finish_loan(self):
        if not self.loan_items:
            self.show_message("Hinweis", "Keine Ausleihe-Einträge vorhanden.")
            return

        self.show_message(
            "Ausleihe abgeschlossen",
            f"Ausleihe gespeichert!\n\nEinträge gesamt: {len(self.loan_items)}"
        )
        self.reset_all()