# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: AusleiheWidget (GUI Design & Sprint-Demo)
# Datei: Ausleihe.py
#
# Autoren: Batuhan Aktürk & Daniel Popp (Entstanden im Pair Programming)
#
# Stand (Epic 8):
# - ECHTER Scanner (UniversalQRScanner) für Schüler und Buch integriert (Jaclyn Barta)
# - Schüler & Buch per Scan ODER manueller Eingabe erfassen (Fallback)
# - DATENBANK-ANBINDUNG: Dummy-Daten entfernt, Live-Abfrage aus der MariaDB
# - Historienanzeige zieht sich "Bereits ausgeliehene Bücher" aus der DB
# - Ausleihe speichert Buchungen live in der Datenbank
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
from database_manager import DatabaseManager  # <--- WICHTIG: DB-Import hinzugefügt


# ==============================================================================
# Haupt-Widget: AusleiheWidget
# ==============================================================================
class AusleiheWidget(QWidget):
    COLOR = "#8DBF42"
    ALT_COLOR = "#007BFF"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # --- NEU: Datenbank initialisieren ---
        self.db = DatabaseManager()

        # Zustand des aktuellen Ausleihvorgangs
        self.current_student = None
        self.loan_items = []

        # WICHTIG: Die Dummy-Daten wurden hier komplett entfernt!

        # ----------------------------------------------------------------------
        # Layout-Aufbau (Daniel Popp)
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

        self.btn_scan_book = QPushButton("Buch scannen")
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
        bottom_actions = QHBoxLayout()
        bottom_actions.setContentsMargins(10, 10, 10, 0)
        bottom_actions.addStretch()

        self.btn_next_student = QPushButton("Zurücksetzen")
        self.btn_next_student.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 12px 25px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { border: 3px solid #333333; }
        """)
        self.btn_next_student.clicked.connect(self.reset_all)
        self.btn_next_student.setEnabled(False)
        bottom_actions.addWidget(self.btn_next_student)

        self.btn_finish = QPushButton("Ausleihe abschließen")
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
    # Hilfsfunktionen
    # --------------------------------------------------------------------------
    def get_image_path(self, filename):
        return resource_path_any(os.path.join("pic", filename), os.path.join("..", "pic", filename))

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
    # Schüler Logik (DATENBANK INTEGRATION)
    # ==============================================================================
    def manual_student_enter(self):
        sid = self.in_student.text().strip()
        if sid:
            self._process_student(sid)

    def scan_student(self):
        scanner = UniversalQRScanner(
            parent=self,
            target_mode="STUDENT",
            color_theme=self.COLOR,
            context_text="Schülerausweis scannen"
        )

        if scanner.exec() == QDialog.DialogCode.Accepted:
            result = scanner.final_result
            if result:
                # Nutzt die formatierte ID vom Scanner
                student_id = result.get('full_id', result.get('id', ''))
                if student_id:
                    self._process_student(student_id)

    def _process_student(self, sid):
        try:
            # 1. Schüler aus der Datenbank holen
            student_data = self.db.get_student_by_qr_id(sid)

            if not student_data:
                self.show_message("Fehler", f"Schüler mit ID '{sid}' nicht in der Datenbank gefunden!")
                self.in_student.clear()
                return

            # Wir lesen die Daten aus dem Dictionary aus, das der DB-Manager zurückgibt
            s_nachname = student_data.get('nachname', '')
            s_vorname = student_data.get('vorname', '')
            s_klasse = student_data.get('klasse', '')

            student_name = f"{s_vorname} {s_nachname}"

            self.current_student = {
                "id": sid,
                "name": student_name,
                "klasse": s_klasse,
                "db_id": student_data.get('db_id')  # Wichtig fürs Speichern später!
            }

            display = f"{sid} - {student_name} ({s_klasse})"
            self.lbl_student_status.setText(f"✅ Schüler ausgewählt: {display}")
            self.lbl_student_status.setStyleSheet("color: #333333; margin-left: 10px; font-weight: bold;")
            self.in_student.setText(display)

            # 2. Historie aus der DB holen
            try:
                history = self.db.get_active_loans_for_student(sid)
            except AttributeError:
                history = []

            self.lbl_history.setText(f"Bereits ausgeliehene Bücher von {student_name}:")
            self.lbl_history.setStyleSheet("color: #333333; font-weight: bold; margin-left: 10px;")
            self.table_history.setRowCount(len(history))

            for i, item in enumerate(history):
                isbn = str(item[0]) if isinstance(item, tuple) else item.get('isbn', '')
                titel = str(item[1]) if isinstance(item, tuple) else item.get('titel', '')
                self.table_history.setItem(i, 0, QTableWidgetItem(isbn))
                self.table_history.setItem(i, 1, QTableWidgetItem(titel))

            self.lbl_history.show()
            self.table_history.show()

            self.in_book.setEnabled(True)
            self.btn_manual_book.setEnabled(True)
            self.btn_scan_book.setEnabled(True)
            self.btn_finish.setEnabled(True)
            self.btn_next_student.setEnabled(True)
            self.in_book.setFocus()

        except Exception as e:
            self.show_message("Datenbank-Fehler", f"Konnte Schüler nicht abrufen:\n{e}")

    # ==============================================================================
    # Buch Logik (DATENBANK INTEGRATION)
    # ==============================================================================
    def manual_book_enter(self):
        isbn = self.in_book.text().strip()
        if isbn:
            self._process_book(isbn)

    def scan_book(self):
        if not self.current_student:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler scannen oder eingeben.")
            return

        scanner = UniversalQRScanner(
            parent=self,
            target_mode="BOOK",
            color_theme=self.COLOR,
            context_text="Buch scannen"
        )

        if scanner.exec() == QDialog.DialogCode.Accepted:
            result = scanner.final_result
            if result:
                isbn = result.get('isbn', result.get('id', ''))
                self._process_book(isbn)

    def _process_book(self, isbn):
        if not self.current_student:
            self.show_message("Hinweis", "Bitte zuerst einen Schüler auswählen.")
            return

        try:
            # 1. Ist das Buch schon in unserer aktuellen Ausleih-Liste?
            if any(x["student_id"] == self.current_student["id"] and x["isbn"] == isbn for x in self.loan_items):
                self.show_message("Hinweis", "Dieses Buch ist für diesen Schüler bereits in der Liste.")
                self.in_book.clear()
                self.in_book.setFocus()
                return

            # 2. Buch aus der Datenbank holen
            book_data = self.db.get_book_by_qr_data(isbn)
            if not book_data:
                self.show_message("Fehler", f"Buch mit ISBN '{isbn}' nicht im System gefunden!")
                self.in_book.clear()
                self.in_book.setFocus()
                return

            b_titel = book_data.get('titel', 'Unbekannt')
            b_verlag = book_data.get('verlag', '-')
            b_auflage = book_data.get('auflage', '-')

            student_display = f"{self.current_student['id']} - {self.current_student['name']} ({self.current_student['klasse']})"

            self.loan_items.append({
                "student_id": self.current_student["id"],
                "student_display": student_display,
                "isbn": isbn,
                "titel": b_titel,
                "verlag": b_verlag,
                "auflage": b_auflage,
            })

            self.reload_table()
            self.in_book.clear()
            self.in_book.setFocus()

        except Exception as e:
            self.show_message("Datenbank-Fehler", f"Konnte Buch nicht prüfen:\n{e}")

    # ==============================================================================
    # Tabellen & Reset Logik
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

    def remove_item(self, row_index):
        if row_index < 0 or row_index >= len(self.loan_items):
            return
        self.loan_items.pop(row_index)
        self.reload_table()

    def reset_all(self):
        self.current_student = None
        self.loan_items = []
        self.in_student.clear()
        self.in_book.clear()
        self.table_history.setRowCount(0)
        self.table_history.hide()
        self.lbl_history.hide()

        self.in_book.setEnabled(False)
        self.btn_manual_book.setEnabled(False)
        self.btn_scan_book.setEnabled(False)
        self.btn_finish.setEnabled(False)
        self.btn_next_student.setEnabled(False)

        self.lbl_student_status.setText("Kein Schüler ausgewählt.")
        self.lbl_student_status.setStyleSheet("color: #666666; margin-left: 10px;")

        self.reload_table()
        self.in_student.setFocus()

    # ==============================================================================
    # DATENBANK: Ausleihe endgültig speichern
    # ==============================================================================
    def finish_loan(self):
        if not self.loan_items:
            self.show_message("Hinweis", "Keine Ausleihe-Einträge vorhanden.")
            return

        try:
            erfolgreich = 0
            for item in self.loan_items:
                # Holt sich die echte formatierte ID (z.B. MB_2024-25_015)
                qr_id = item["student_id"]
                isbn = item["isbn"]

                # Ruft die neue Funktion in der Datenbank auf
                self.db.add_loan(qr_id, isbn)
                erfolgreich += 1

            self.show_message(
                "Ausleihe abgeschlossen",
                f"Ausleihe erfolgreich gespeichert!\n\nVerbuchte Bücher: {erfolgreich}"
            )
            self.reset_all()

        except Exception as e:
            self.show_message("Datenbank-Fehler", f"Fehler beim Speichern der Ausleihe:\n{e}")