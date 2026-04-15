# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
#
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
#   Bücher geladen und in der Tabelle visualisiert.
# - "Nächster Schüler"-Funktion: Vollständiger Reset der Ansicht und der Tabelle.
# - Rückgabe-Logik: "Buch scannen (Rückgabe)" prüft die ISBN gegen die geladene
#   Liste und verarbeitet die Rückgabe.
# - UI/UX: Anpassung an das Design der Ausleihe.
#
# Erweiterung / Überarbeitung im Team:
# - Batuhan Aktürk:
#   Mitarbeit an der Erweiterung der Rückgabe-Logik gemäß PBI 7.4,
#   insbesondere bei der fachlichen Prüfung des Rückgabeablaufs,
#   der Kommentierung, der Fehlerfall-Betrachtung und der Unterstützung
#   bei der Verarbeitung von Scan- und Rückgabeschritten.
#
# - Harun:
#   Mitarbeit an der Erweiterung der Rückgabe-Logik gemäß PBI 7.4,
#   insbesondere bei der Strukturierung des Ablaufs, der fachlichen
#   Einordnung der Rückgabeschritte, der Verarbeitung von Scan-Ergebnissen
#   sowie der gemeinsamen Ausarbeitung der Rückgabeprüfung und Fehlerszenarien.
#
# Refactoring-Hinweis:
# - Header, Breadcrumb, Seitentitel und Footer werden jetzt zentral
#   über BasePageWidget bereitgestellt.
# - Dadurch wird Code-Duplikation reduziert und das Layout ist
#   konsistent mit den anderen GUI-Ansichten.
# ------------------------------------------------------------------------------

import os
import sqlite3
from datetime import datetime

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog, QComboBox, QInputDialog, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app_paths import resource_path_any
from base_page import BasePageWidget

# ==============================================================================
# Gemeinsame Styles
# Zweck:
# - Vereinheitlichung der Rundungen und Hover-Effekte
# - Sichtbare Rückmeldung beim Überfahren mit der Maus
# ==============================================================================
BUTTON_RADIUS = 10


def primary_button_style(color: str) -> str:
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            padding: 10px 18px;
            border: 3px solid {color};
            border-radius: {BUTTON_RADIUS}px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            border: 3px solid #333333;
            background-color: {color};
        }}
        QPushButton:pressed {{
            background-color: #444444;
            border: 3px solid #444444;
        }}
        QPushButton:disabled {{
            background-color: #CFCFCF;
            border: 3px solid #CFCFCF;
            color: #888888;
        }}
    """


def neutral_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: #E0E0E0;
            color: #333333;
            padding: 10px 18px;
            border: 3px solid #E0E0E0;
            border-radius: {BUTTON_RADIUS}px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            border: 3px solid #333333;
            background-color: #D7D7D7;
        }}
        QPushButton:pressed {{
            background-color: #444444;
            border: 3px solid #444444;
            color: white;
        }}
    """


def input_style(accent_color: str) -> str:
    return f"""
        QLineEdit {{
            padding: 10px;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            background-color: #FFFFFF;
            color: #333333;
            font-size: 14px;
        }}
        QLineEdit:hover {{
            border: 1px solid #999999;
        }}
        QLineEdit:focus {{
            border: 2px solid {accent_color};
        }}
        QLineEdit:disabled {{
            background-color: #F3F3F3;
            color: #888888;
        }}
    """


def combo_style(accent_color: str) -> str:
    return f"""
        QComboBox {{
            background: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            padding: 10px;
            color: #333333;
            font-size: 14px;
        }}
        QComboBox:hover {{
            border: 1px solid #999999;
        }}
        QComboBox:focus {{
            border: 2px solid {accent_color};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox QAbstractItemView {{
            background: #FFFFFF;
            color: #333333;
            border: 1px solid #CFCFCF;
            selection-background-color: #E0E0E0;
            selection-color: #000000;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: #ECECEC;
            color: #000000;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: #DADADA;
            color: #000000;
        }}
    """


# ==============================================================================
# FakeScanDialog
# Zweck:
# - Demo-Dialog für den Scan-Vorgang (Jaclyn Barta).
# - Simuliert die Kamera-Erkennung für die Sprint-Präsentation.
#
# Erweiterte Nutzung im Team:
# - Batuhan Aktürk:
#   Mitarbeit bei der Nutzung des Dialogs für die Rückgabe per Scan,
#   damit der Ablauf für Schüler und Buch nachvollziehbar demonstriert
#   und geprüft werden kann.
# - Harun:
#   Mitarbeit bei der Nutzung des Dialogs für die Rückgabe per Scan,
#   damit der Ablauf logisch strukturiert und für den Sprint
#   konsistent verwendet werden kann.
# ==============================================================================
class FakeScanDialog(QDialog):
    def __init__(self, parent=None, title="QR scannen", items=None, color="#E57368", allow_manual=True):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setFixedSize(760, 560)
        self.result_text = None
        self._color = color
        self._items = items or []
        self._allow_manual = allow_manual

        self.setStyleSheet(f"""
            QDialog {{
                background: #FFFFFF;
            }}

            QLabel {{
                color: #333333;
                background: transparent;
            }}

            QComboBox {{
                background: #FFFFFF;
                border: 1px solid #CFCFCF;
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px 12px;
                color: #333333;
                min-height: 22px;
            }}

            QComboBox:hover {{
                border: 1px solid #B8B8B8;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 34px;
            }}

            QComboBox::down-arrow {{
                image: none;
            }}

            QComboBox QAbstractItemView {{
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #CFCFCF;
                selection-background-color: #EAEAEA;
                selection-color: #333333;
                outline: 0px;
                padding: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.lbl_info = QLabel("📷 Kamera aktiv… Halte den QR-Code vor die Kamera.")
        self.lbl_info.setFont(QFont("Open Sans", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_info)

        self.video_placeholder = QLabel(
            "LIVE-KAMERA (Demo)\n\n[Hier wird im nächsten Sprint der OpenCV-Stream angezeigt]"
        )
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setMinimumSize(640, 340)
        self.video_placeholder.setStyleSheet(f"""
            border: 1px solid #D8D8D8;
            border-radius: 12px;
            background: #F7F7F7;
            color: #666666;
            font-size: 16px;
        """)
        layout.addWidget(self.video_placeholder)

        self.lbl_status = QLabel("Status: Warte auf Scan…")
        self.lbl_status.setStyleSheet("color:#666666; font-size:14px;")
        layout.addWidget(self.lbl_status)

        self.combo = QComboBox()
        self.combo.addItem("Bitte auswählen (Demo)…")
        for x in self._items:
            self.combo.addItem(x)
        self.combo.setStyleSheet(combo_style(color))
        layout.addWidget(self.combo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_manual = QPushButton("Manuell eingeben")
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_demo_scan = QPushButton("Demo-Scan")

        self.btn_manual.setStyleSheet(neutral_button_style())
        self.btn_cancel.setStyleSheet(neutral_button_style())
        self.btn_demo_scan.setStyleSheet(primary_button_style(self._color))

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_demo_scan.clicked.connect(self._do_demo_scan)
        self.btn_manual.clicked.connect(self._manual_input)

        if self._allow_manual:
            btn_row.addWidget(self.btn_manual)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_demo_scan)
        layout.addLayout(btn_row)

    def _do_demo_scan(self):
        """
        Übernimmt den gewählten Demo-Eintrag als Scan-Ergebnis.
        """
        picked = self.combo.currentText()
        if picked.startswith("Bitte auswählen"):
            QMessageBox.warning(self, "Hinweis", "Bitte zuerst einen Demo-Eintrag auswählen.")
            return

        self.result_text = picked
        self.accept()

    def _manual_input(self):
        """
        Ermöglicht eine manuelle Eingabe, falls ein QR-Code
        nicht scanbar ist. Das ist Teil der PBI-Anforderung.
        """
        text, ok = QInputDialog.getText(
            self,
            "Manuelle Eingabe",
            "Bitte Schüler-ID oder Buchcode / ISBN eingeben:"
        )

        if ok and text.strip():
            self.result_text = text.strip()
            self.accept()


# ==============================================================================
# ZustandDialog
# Zweck:
# - Optionaler Dialog zur Erfassung des Buchzustands bei Rückgabe.
#
# Team-Erweiterung:
# - Batuhan Aktürk:
#   Mitarbeit an der fachlichen Ergänzung des optionalen Zustands,
#   damit Schäden nachvollziehbar bleiben.
# - Harun:
#   Mitarbeit an der Einordnung des Zustandsdialogs als optionalen
#   Teil der Rückgabe gemäß User Story.
# ==============================================================================
class ZustandDialog(QDialog):
    def __init__(self, parent=None, color="#E57368"):
        super().__init__(parent)
        self.setWindowTitle("Zustand des Buches")
        self.setFixedSize(430, 190)
        self.setStyleSheet("background:#FFFFFF;")

        self.selected_condition = "In Ordnung"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Bitte Zustand des Buches auswählen:")
        lbl.setFont(QFont("Open Sans", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.addItems([
            "In Ordnung",
            "Leicht beschädigt",
            "Stark beschädigt"
        ])
        self.combo.setStyleSheet(combo_style(color))
        layout.addWidget(self.combo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Abbrechen")
        btn_ok = QPushButton("Übernehmen")

        btn_cancel.setStyleSheet(neutral_button_style())
        btn_ok.setStyleSheet(primary_button_style(color))

        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._accept_condition)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _accept_condition(self):
        """
        Speichert die Auswahl und bestätigt den Dialog.
        """
        self.selected_condition = self.combo.currentText()
        self.accept()


# ==============================================================================
# Haupt-Widget: RueckgabeWidget
# ==============================================================================
class RueckgabeWidget(BasePageWidget):
    COLOR_RED = "#E57368"

    def __init__(self, parent=None, db_path=None):
        super().__init__(
            breadcrumb_text="Startseite > Hauptmenü > Rückgabe",
            page_title="Rückgabe",
            accent_color=self.COLOR_RED,
            parent=parent
        )

        self.db_path = db_path or resource_path_any(
            os.path.join("data", "booktrackqr.db"),
            os.path.join("..", "data", "booktrackqr.db"),
            "booktrackqr.db"
        )

        self.current_student_id = None
        self.current_student_display = ""
        self.current_loans = []

        # Dummy-Daten als Fallback, falls keine DB gefunden wird
        self.dummy_loans = {
            "101": [
                {
                    "ausleihe_id": 1,
                    "exemplar_id": 1,
                    "book_code": "BOOK|9783123456789",
                    "isbn": "9783123456789",
                    "titel": "Mathe 5",
                    "zustand": "-"
                },
                {
                    "ausleihe_id": 2,
                    "exemplar_id": 2,
                    "book_code": "BOOK|9783120000001",
                    "isbn": "9783120000001",
                    "titel": "Deutsch 6",
                    "zustand": "-"
                }
            ],
            "102": [
                {
                    "ausleihe_id": 3,
                    "exemplar_id": 3,
                    "book_code": "BOOK|9783129999999",
                    "isbn": "9783129999999",
                    "titel": "Englisch 7",
                    "zustand": "-"
                }
            ]
        }

        self._ensure_return_log_table()

        info_text = QLabel(
            "Ablauf: Schüler scannen oder ID eingeben → ausgeliehene Bücher anzeigen → "
            "Buch scannen/eingeben → Zustand auswählen → Rückgabe übernehmen."
        )
        info_text.setStyleSheet("color:#333333; font-size:15px;")
        self.content_layout.addWidget(info_text)

        # --- SCHÜLERBEREICH ---
        student_row = QHBoxLayout()

        self.in_student = QLineEdit()
        self.in_student.setPlaceholderText("Schüler-ID eingeben oder scannen...")
        self.in_student.setStyleSheet(input_style(self.COLOR_RED))

        self.btn_take_student = QPushButton("Übernehmen")
        self.btn_take_student.setStyleSheet(primary_button_style(self.COLOR_RED))
        self.btn_take_student.clicked.connect(self.take_student_from_input)

        self.btn_scan_student = QPushButton("Schülerausweis scannen")
        self.btn_scan_student.setStyleSheet(primary_button_style(self.COLOR_RED))
        self.btn_scan_student.clicked.connect(self.scan_student)

        student_row.addWidget(self.in_student, 1)
        student_row.addWidget(self.btn_take_student)
        student_row.addWidget(self.btn_scan_student)
        self.content_layout.addLayout(student_row)

        self.lbl_student_selected = QLabel("")
        self.lbl_student_selected.setStyleSheet("color:#2E7D32; font-size:15px; font-weight:bold;")
        self.content_layout.addWidget(self.lbl_student_selected)

        # --- BUCHBEREICH ---
        book_row = QHBoxLayout()

        self.in_book = QLineEdit()
        self.in_book.setPlaceholderText("ISBN oder Buchcode eingeben / scannen...")
        self.in_book.setStyleSheet(input_style(self.COLOR_RED))

        self.btn_take_book = QPushButton("Übernehmen")
        self.btn_take_book.setStyleSheet(primary_button_style(self.COLOR_RED))
        self.btn_take_book.setEnabled(False)
        self.btn_take_book.clicked.connect(self.return_book_from_input)

        self.btn_scan_book = QPushButton("QR-Code scannen")
        self.btn_scan_book.setStyleSheet(primary_button_style(self.COLOR_RED))
        self.btn_scan_book.setEnabled(False)
        self.btn_scan_book.clicked.connect(self.scan_book_return)

        book_row.addWidget(self.in_book, 1)
        book_row.addWidget(self.btn_take_book)
        book_row.addWidget(self.btn_scan_book)
        self.content_layout.addLayout(book_row)

        # --- EINE ZENTRALE TABELLE ---
        self.lbl_open_returns = QLabel("Aktuell ausgeliehene / offene Rückgaben des ausgewählten Schülers:")
        self.lbl_open_returns.setStyleSheet("color:#333333; font-size:15px; font-weight:bold;")
        self.content_layout.addWidget(self.lbl_open_returns)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Buchcode", "ISBN", "Titel", "Zustand"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setMinimumHeight(320)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #D9D9D9;
                border-radius: 12px;
                gridline-color: #E5E5E5;
                background: #FFFFFF;
            }}
            QHeaderView::section {{
                background-color: #F0F0F0;
                border: none;
                border-bottom: 3px solid {self.COLOR_RED};
                font-weight: bold;
                padding: 8px;
            }}
        """)
        self.content_layout.addWidget(self.table)

        # --- BUTTONS UNTEN ---
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.btn_reset = QPushButton("Zurücksetzen")
        self.btn_reset.setStyleSheet(neutral_button_style())
        self.btn_reset.clicked.connect(self.reset_view)

        self.btn_finish = QPushButton("Rückgabe abschließen")
        self.btn_finish.setStyleSheet(primary_button_style(self.COLOR_RED))
        self.btn_finish.clicked.connect(self.finish_return_process)
        self.btn_finish.setEnabled(False)

        bottom_row.addWidget(self.btn_reset)
        bottom_row.addWidget(self.btn_finish)
        self.content_layout.addLayout(bottom_row)

    # --------------------------------------------------------------------------
    # DB-HILFSMETHODEN
    # --------------------------------------------------------------------------
    def _connect_db(self):
        if not self.db_path or not os.path.exists(self.db_path):
            return None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_return_log_table(self):
        """
        Rückgabe-Protokoll anlegen, damit Zustände nachvollziehbar bleiben.
        """
        conn = self._connect_db()
        if conn is None:
            return

        try:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS RueckgabeProtokoll
                         (
                             rueckgabe_id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             student_id
                             TEXT
                             NOT
                             NULL,
                             exemplar_id
                             INTEGER
                             NOT
                             NULL,
                             isbn
                             TEXT,
                             titel
                             TEXT,
                             buchcode
                             TEXT,
                             rueckgabe_am
                             TEXT
                             NOT
                             NULL,
                             zustand
                             TEXT
                             NOT
                             NULL
                         )
                         """)
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    def get_student_demo_items(self):
        """
        Demo-Liste für Scan.
        Erst DB versuchen, sonst Fallback.
        """
        conn = self._connect_db()
        if conn is not None:
            try:
                rows = conn.execute("""
                                    SELECT s.student_id,
                                           s.vorname,
                                           s.nachname,
                                           COALESCE(sk.name, '') AS klasse
                                    FROM Studierende s
                                             LEFT JOIN Schulklasse sk ON s.schulklasse_id = sk.schulklasse_id
                                    ORDER BY s.student_id LIMIT 50
                                    """).fetchall()

                items = []
                for row in rows:
                    student_id = str(row["student_id"])
                    vorname = row["vorname"] or ""
                    nachname = row["nachname"] or ""
                    klasse = row["klasse"] or ""
                    if klasse:
                        items.append(f"{student_id} - {vorname} {nachname} ({klasse})".strip())
                    else:
                        items.append(f"{student_id} - {vorname} {nachname}".strip())

                if items:
                    return items

            except sqlite3.Error:
                pass
            finally:
                conn.close()

        return [
            "101 - Max Müller (10A)",
            "102 - Lisa Schmidt (10A)",
            "201 - Ali Yilmaz (11B)"
        ]

    def get_student_display_name(self, student_id):
        """
        Schülername schön anzeigen.
        """
        conn = self._connect_db()
        if conn is not None:
            try:
                row = conn.execute("""
                                   SELECT s.student_id,
                                          s.vorname,
                                          s.nachname,
                                          COALESCE(sk.name, '') AS klasse
                                   FROM Studierende s
                                            LEFT JOIN Schulklasse sk ON s.schulklasse_id = sk.schulklasse_id
                                   WHERE s.student_id = ?
                                   """, (student_id,)).fetchone()

                if row:
                    vorname = row["vorname"] or ""
                    nachname = row["nachname"] or ""
                    klasse = row["klasse"] or ""
                    if klasse:
                        return f"{student_id} - {vorname} {nachname} ({klasse})".strip()
                    return f"{student_id} - {vorname} {nachname}".strip()

            except sqlite3.Error:
                pass
            finally:
                conn.close()

        return str(student_id)

    def load_student_books_from_db(self, student_id):
        """
        Aktuelle Ausleihen des Schülers aus DB laden.
        """
        conn = self._connect_db()
        if conn is None:
            return None

        try:
            rows = conn.execute("""
                                SELECT a.ausleihe_id,
                                       a.student_id,
                                       a.exemplar_id,
                                       COALESCE(b.qr_code, '') AS book_code,
                                       COALESCE(t.isbn, '')    AS isbn,
                                       COALESCE(t.titel, '')   AS titel
                                FROM Ausleihe_Aktuell a
                                         JOIN BuchExemplar b ON a.exemplar_id = b.exemplar_id
                                         JOIN BuchTitel t ON b.titel_id = t.titel_id
                                WHERE a.student_id = ?
                                ORDER BY t.titel
                                """, (student_id,)).fetchall()

            result = []
            for row in rows:
                result.append({
                    "ausleihe_id": row["ausleihe_id"],
                    "student_id": row["student_id"],
                    "exemplar_id": row["exemplar_id"],
                    "book_code": row["book_code"] or "",
                    "isbn": row["isbn"] or "",
                    "titel": row["titel"] or "",
                    "zustand": "-"
                })

            return result

        except sqlite3.Error:
            return None
        finally:
            conn.close()

    def process_return_in_db(self, book, student_id, selected_condition):
        """
        Rückgabe in DB übernehmen:
        1. Protokoll schreiben
        2. Ausleihe_Aktuell löschen
        """
        conn = self._connect_db()
        if conn is None:
            return False, "Keine Datenbank gefunden."

        try:
            conn.execute("BEGIN")

            conn.execute("""
                         INSERT INTO RueckgabeProtokoll (student_id, exemplar_id, isbn, titel, buchcode, rueckgabe_am,
                                                         zustand)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                         """, (
                             str(student_id),
                             int(book["exemplar_id"]),
                             book["isbn"],
                             book["titel"],
                             book["book_code"],
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             selected_condition
                         ))

            conn.execute("""
                         DELETE
                         FROM Ausleihe_Aktuell
                         WHERE ausleihe_id = ?
                         """, (int(book["ausleihe_id"]),))

            conn.commit()
            return True, None

        except sqlite3.Error as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    # --------------------------------------------------------------------------
    # UI-HILFSMETHODEN
    # --------------------------------------------------------------------------
    def refresh_table(self):
        """
        Nur eine zentrale Tabelle:
        zeigt die aktuell noch offenen Rückgaben / ausgeliehenen Bücher.
        """
        self.table.setRowCount(len(self.current_loans))

        for row, book in enumerate(self.current_loans):
            self.table.setItem(row, 0, QTableWidgetItem(book["book_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(book["isbn"]))
            self.table.setItem(row, 2, QTableWidgetItem(book["titel"]))
            self.table.setItem(row, 3, QTableWidgetItem(book.get("zustand", "-")))

    def normalize_book_input(self, text):
        """
        Vereinheitlicht Eingaben:
        - BOOK|978...
        - 978...
        """
        raw = text.strip()

        if raw.startswith("BOOK|"):
            isbn_only = raw.replace("BOOK|", "").strip()
            normalized_code = raw
        else:
            isbn_only = raw
            normalized_code = f"BOOK|{raw}"

        return normalized_code, isbn_only

    def show_message(self, title, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #FFFFFF;
            }}
            QLabel {{
                color: #333333;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: #E0E0E0;
                color: #333333;
                padding: 8px 16px;
                border-radius: {BUTTON_RADIUS}px;
                border: 1px solid #CCCCCC;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #D0D0D0;
                border: 1px solid #333333;
            }}
        """)
        msg.exec()

    # --------------------------------------------------------------------------
    # SCHÜLERLOGIK
    # --------------------------------------------------------------------------
    def scan_student(self):
        items = self.get_student_demo_items()
        d = FakeScanDialog(
            self,
            title="Schüler QR scannen (Demo)",
            items=items,
            color=self.COLOR_RED,
            allow_manual=True
        )

        if d.exec() == QDialog.DialogCode.Accepted:
            picked = d.result_text.strip()
            self.in_student.setText(picked)
            self.take_student_from_input()

    def take_student_from_input(self):
        raw = self.in_student.text().strip()
        if not raw:
            self.show_message("Hinweis", "Bitte zuerst eine Schüler-ID eingeben oder scannen.",
                              QMessageBox.Icon.Warning)
            return

        if " - " in raw:
            student_id = raw.split(" - ")[0].strip()
        else:
            student_id = raw

        self.current_student_id = student_id
        self.current_student_display = self.get_student_display_name(student_id)
        self.load_student_books()

    def load_student_books(self):
        books = self.load_student_books_from_db(self.current_student_id)

        if books is None:
            books = [book.copy() for book in self.dummy_loans.get(self.current_student_id, [])]

        self.current_loans = books

        # schönere Anzeige
        if self.current_student_display:
            self.lbl_student_selected.setText(f"✅ Schüler ausgewählt: {self.current_student_display}")
        else:
            self.lbl_student_selected.setText(f"✅ Schüler ausgewählt: {self.current_student_id}")

        self.refresh_table()

        has_books = len(books) > 0
        self.btn_scan_book.setEnabled(has_books)
        self.btn_take_book.setEnabled(has_books)
        self.btn_finish.setEnabled(has_books)

        if not has_books:
            self.show_message(
                "Hinweis",
                "Für diesen Schüler sind aktuell keine ausgeliehenen Bücher vorhanden."
            )

    # --------------------------------------------------------------------------
    # RÜCKGABELOGIK
    # --------------------------------------------------------------------------
    def scan_book_return(self):
        if not self.current_student_id:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler scannen.", QMessageBox.Icon.Warning)
            return

        demo_items = []
        for book in self.current_loans:
            if book["book_code"]:
                demo_items.append(book["book_code"])
            if book["isbn"]:
                demo_items.append(book["isbn"])

        d = FakeScanDialog(
            self,
            title="Buch-Scan Rückgabe (Demo)",
            items=demo_items,
            color=self.COLOR_RED,
            allow_manual=True
        )

        if d.exec() != QDialog.DialogCode.Accepted:
            return

        scanned_text = d.result_text.strip()
        self.process_book_return(scanned_text)

    def return_book_from_input(self):
        scanned_text = self.in_book.text().strip()
        if not scanned_text:
            self.show_message("Hinweis", "Bitte zuerst ISBN oder Buchcode eingeben.", QMessageBox.Icon.Warning)
            return

        self.process_book_return(scanned_text)

    def process_book_return(self, scanned_text):
        if not self.current_student_id:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler scannen.", QMessageBox.Icon.Warning)
            return

        normalized_code, isbn_only = self.normalize_book_input(scanned_text)

        found_index = -1
        found_book = None

        for row, book in enumerate(self.current_loans):
            if book["book_code"] == normalized_code or book["isbn"] == isbn_only:
                found_index = row
                found_book = book
                break

        # Typischer Fehlerfall laut PBI:
        # Buch nicht gefunden / nicht ausgeliehen -> Meldung, keine Datenänderung
        if found_book is None:
            self.show_message(
                "Fehlhinweis",
                "Das gescannte Buch ist diesem Schüler nicht zugeordnet oder aktuell nicht ausgeliehen.\n\n"
                "Es wurde keine Datenänderung durchgeführt.",
                QMessageBox.Icon.Critical
            )
            return

        zustand_dialog = ZustandDialog(self, color=self.COLOR_RED)
        if zustand_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_condition = zustand_dialog.selected_condition

        success, db_error = self.process_return_in_db(
            found_book,
            self.current_student_id,
            selected_condition
        )

        # Fallback ohne DB
        if not success and db_error == "Keine Datenbank gefunden.":
            found_book["zustand"] = selected_condition
            self.current_loans.pop(found_index)

            original_books = self.dummy_loans.get(self.current_student_id, [])
            for i, original_book in enumerate(original_books):
                if (
                        original_book["book_code"] == normalized_code
                        or original_book["isbn"] == isbn_only
                ):
                    original_books.pop(i)
                    break
        elif not success:
            self.show_message(
                "Datenbankfehler",
                f"Die Rückgabe konnte nicht gespeichert werden.\n\n{db_error}",
                QMessageBox.Icon.Critical
            )
            return
        else:
            self.current_loans.pop(found_index)

        self.refresh_table()
        self.in_book.clear()

        self.show_message(
            "Erfolg",
            f"Buch {isbn_only} erfolgreich zurückgegeben.\nZustand: {selected_condition}"
        )

        if len(self.current_loans) == 0:
            self.btn_scan_book.setEnabled(False)
            self.btn_take_book.setEnabled(False)
            self.btn_finish.setEnabled(False)
            self.show_message(
                "Abgeschlossen",
                "Alle ausgeliehenen Bücher dieses Schülers wurden zurückgegeben."
            )

    # --------------------------------------------------------------------------
    # ABSCHLUSS / RESET
    # --------------------------------------------------------------------------
    def finish_return_process(self):
        if not self.current_student_id:
            self.show_message("Hinweis", "Es ist aktuell kein Schüler ausgewählt.", QMessageBox.Icon.Warning)
            return

        self.show_message(
            "Rückgabe abgeschlossen",
            "Der Rückgabevorgang wurde abgeschlossen."
        )
        self.reset_view()

    def reset_view(self):
        self.in_student.clear()
        self.in_book.clear()
        self.lbl_student_selected.clear()
        self.table.setRowCount(0)
        self.btn_scan_book.setEnabled(False)
        self.btn_take_book.setEnabled(False)
        self.btn_finish.setEnabled(False)
        self.current_student_id = None
        self.current_student_display = ""
        self.current_loans = []
