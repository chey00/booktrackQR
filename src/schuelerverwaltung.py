# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: Gesamte Verwaltung (Schüler, Klassen, Schuljahre)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Sprint 4 Autor: Mustafa Demiral (Dynamische ID-Kalkulation, Mac-Design-Fixes)
# Sprint 5 Autor: Mustafa Demiral (Soft-Delete & Admin-Löschung für Schüler)
# Stand: Soft-Delete implementiert, Löschen nur mit Admin-Passwort, Design stabil
# ------------------------------------------------------------------------------

import os
import csv
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,
    QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QBrush
from database_manager import DatabaseManager
from app_paths import resource_path_any


def get_btn_style(bg_color, text_color="white"):
    return f"""
    QPushButton {{ background-color: {bg_color}; color: {text_color}; padding: 8px 20px;
    border: 3px solid {bg_color}; border-radius: 6px; font-weight: bold; font-size: 14px; }}
    QPushButton:hover, QPushButton:focus {{ border: 3px solid #000000; }}
    QPushButton:pressed {{ background-color: #444444; border: 3px solid #000000; color: white; }}
    """


def get_import_btn_style():
    return """
    QPushButton {
        background-color: #FFFFFF; color: #333333; padding: 8px 20px;
        border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 14px;
    }
    QPushButton:hover, QPushButton:focus { border: 3px solid #000000; }
    QPushButton:pressed { background-color: #F0F0F0; border: 3px solid #000000; color: #333333; }
    """


# --- Standard Dialog für Klassen und Jahre ---
class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None, warning_text="⚠️ Möchten Sie diesen Datensatz wirklich\nunwiderruflich löschen?"):
        super().__init__(parent)
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(450, 180)
        self.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(self)
        self.label = QLabel(warning_text)
        self.label.setFont(QFont("Open Sans", 11, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(self.label)
        btn_layout = QHBoxLayout()
        self.btn_no = QPushButton("Abbrechen")
        self.btn_yes = QPushButton("Löschen")
        self.btn_yes.setStyleSheet(get_btn_style("#D32F2F"))
        self.btn_no.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)


# --- MUSTAFA DEMIRAL (Sprint 5): Neuer Dialog für Schüler (Soft-Delete vs. Passwort-Delete) ---
# --- Passwort hierfür ist "admin123" ---
class StudentDeleteDialog(QDialog):
    def __init__(self, parent=None, student_name=""):
        super().__init__(parent)
        self.setWindowTitle("Schüler verwalten")
        self.setFixedSize(480, 260)
        self.setStyleSheet("background-color: #FFFFFF; color: #333333;")

        self.result_action = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        info_text = (f"Was möchten Sie mit dem Schüler '{student_name}' tun?\n\n"
                     "DEAKTIVIEREN: Schüler verschwindet aus der Liste, bleibt aber als Archiv im System.\n\n"
                     "LÖSCHEN: Schüler wird unwiderruflich gelöscht (Nur mit Admin-Passwort).")

        lbl = QLabel(info_text)
        lbl.setFont(QFont("Open Sans", 10))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Admin-Passwort (nur für endgültiges Löschen)")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px; font-size: 14px;")
        layout.addWidget(self.pw_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_deactivate = QPushButton("Deaktivieren")
        self.btn_delete = QPushButton("Endgültig Löschen")

        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_deactivate.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_delete.setStyleSheet(get_btn_style("#D32F2F"))

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_deactivate.clicked.connect(self.do_deactivate)
        self.btn_delete.clicked.connect(self.do_delete)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_deactivate)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    def do_deactivate(self):
        self.result_action = 'deactivate'
        self.accept()

    def do_delete(self):
        if self.pw_input.text() == "admin123":
            self.result_action = 'delete'
            self.accept()
        else:
            self.error_label.setText("Falsches Admin-Passwort! Löschen verweigert.")


# --- MUSTAFA DEMIRAL (Sprint 5): Neuer Dialog um das komplette Archiv per Admin-Passwort zu leeren ---
class CleanArchiveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Archiv leeren")
        self.setFixedSize(480, 220)
        self.setStyleSheet("background-color: #FFFFFF; color: #333333;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel(
            "Möchten Sie wirklich ALLE inaktiven Schüler endgültig aus dem System löschen?\nDieser Schritt kann nicht rückgängig gemacht werden.")
        lbl.setFont(QFont("Open Sans", 10, QFont.Weight.Bold))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Admin-Passwort eingeben")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px; font-size: 14px;")
        layout.addWidget(self.pw_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_delete = QPushButton("Alle Inaktiven Löschen")

        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_delete.setStyleSheet(get_btn_style("#D32F2F"))

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_delete.clicked.connect(self.do_delete)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    def do_delete(self):
        if self.pw_input.text() == "admin123":
            self.accept()
        else:
            self.error_label.setText("Falsches Admin-Passwort!")


# ==============================================================================
# DIALOGE
# ==============================================================================

class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neuer Schüler" if not student_data else "Schüler bearbeiten")
        self.setFixedSize(400, 380)
        self.setStyleSheet("""
        QDialog { background-color: #FFFFFF; }
        QLabel { color: #333333; font-weight: bold; }
        QLineEdit, QComboBox { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 8px; color: #333333; font-size: 14px; }
        QLineEdit:focus, QComboBox:focus { border: 2px solid #000000; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname eingeben")
        self.input_nachname = QLineEdit()
        self.input_nachname.setPlaceholderText("Nachname eingeben")

        self.combo_klasse = QComboBox()
        self.combo_klasse.addItems(["Bitte wählen...", "MB", "MT", "KI", "WI"])

        self.combo_jahr = QComboBox()
        self.combo_jahr.addItems(["Bitte wählen...", "2023-24", "2024-25", "2025-26", "2026-27"])

        # MUSTAFA DEMIRAL (Sprint 4/5): Neues Layout für die dynamische ID-Anzeige inkl. manueller Eingabe
        self.id_prefix_label = QLabel("..._..._")
        self.id_prefix_label.setStyleSheet("color: #666666; font-style: italic; font-weight: normal;")

        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("Auto")
        self.input_id.setFixedWidth(80)

        id_layout = QHBoxLayout()
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.addWidget(self.id_prefix_label)
        id_layout.addWidget(self.input_id)
        id_layout.addStretch()

        for w in [self.input_vorname, self.input_nachname, self.combo_klasse, self.combo_jahr]:
            w.setFixedWidth(250)

        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        self.combo_klasse.currentTextChanged.connect(self.update_id_prefix)
        self.combo_jahr.currentTextChanged.connect(self.update_id_prefix)

        if student_data:
            display_id = int(student_data[0]) % 10000
            self.input_id.setText(f"{display_id:03d}")
            self.input_nachname.setText(str(student_data[1]))
            self.input_vorname.setText(str(student_data[2]))
            self.combo_klasse.setCurrentText(str(student_data[3]))
            if len(student_data) > 4:
                self.combo_jahr.setCurrentText(str(student_data[4]))
            self.update_id_prefix()

        form_layout.addRow(QLabel("Vorname*:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname*:"), self.input_nachname)
        form_layout.addRow(QLabel("Klasse*:"), self.combo_klasse)
        form_layout.addRow(QLabel("Schuljahr*:"), self.combo_jahr)
        form_layout.addRow(QLabel("ID-Nummer:"), id_layout)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def update_id_prefix(self):
        klasse = self.combo_klasse.currentText()
        jahr = self.combo_jahr.currentText()
        if klasse != "Bitte wählen..." and jahr != "Bitte wählen...":
            safe_jahr = jahr.replace('/', '-')
            self.id_prefix_label.setText(f"{klasse}_{safe_jahr}_")
        else:
            self.id_prefix_label.setText("..._..._")

    def validate_and_save(self):
        valid = True

        def check_field(widget, is_invalid):
            if is_invalid:
                widget.setStyleSheet("border: 2px solid #D32F2F")
                return False
            widget.setStyleSheet("")
            return True

        valid &= check_field(self.input_vorname, not self.input_vorname.text().strip())
        valid &= check_field(self.input_nachname, not self.input_nachname.text().strip())
        valid &= check_field(self.combo_klasse, self.combo_klasse.currentText() == "Bitte wählen...")
        valid &= check_field(self.combo_jahr, self.combo_jahr.currentText() == "Bitte wählen...")

        if not valid:
            self.error_label.show()
        else:
            self.accept()


class KlassenDialog(QDialog):
    def __init__(self, parent=None, klassen_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Klasse" if not klassen_data else "Klasse bearbeiten")
        self.setFixedSize(400, 260)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #333333; font-weight: bold; } 
            QLineEdit, QComboBox { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 8px; color: #333333; font-size: 14px; }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #000000; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. MB")
        self.combo_jahr = QComboBox()
        self.combo_jahr.addItems(["Bitte wählen...", "2023-24", "2024-25", "2025-26", "2026-27"])

        for w in [self.input_name, self.combo_jahr]:
            w.setFixedWidth(250)

        if klassen_data:
            self.input_name.setText(klassen_data[1])
            self.combo_jahr.setCurrentText(klassen_data[2])

        form_layout.addRow(QLabel("Klassenname:"), self.input_name)
        form_layout.addRow(QLabel("Schuljahr:"), self.combo_jahr)
        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)


class SchuljahrDialog(QDialog):
    def __init__(self, parent=None, jahr_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Schuljahr" if not jahr_data else "Schuljahr bearbeiten")
        self.setFixedSize(400, 220)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; } 
            QLabel { color: #333333; font-weight: bold; } 
            QLineEdit { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 8px; color: #333333; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #000000; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. 2025-26")
        self.input_name.setFixedWidth(250)

        if jahr_data:
            self.input_name.setText(jahr_data[1])

        form_layout.addRow(QLabel("Schuljahr:"), self.input_name)
        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)


# ==============================================================================
# TABS
# ==============================================================================

class BaseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 25, 15, 15)
        self.main_layout.setSpacing(15)
        self.input_style = "padding: 12px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(get_btn_style("#F1BD4D"))

    def setup_table(self, col_count, headers):
        self.table = QTableWidget(0, col_count)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                alternate-background-color: #F9F9F9;
                border: 1px solid #E0E0E0; 
                border-radius: 8px; 
                gridline-color: #EDEDED;
                color: #000000; 
                font-size: 14px;
            }
        """)

        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section { 
                background-color: #F0F0F0; 
                color: #333333;
                font-weight: bold; 
                border: none;
                border-bottom: 3px solid #F1BD4D; 
                padding: 12px; 
            }
        """)

        self.main_layout.addWidget(self.table)

    def show_popup(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(
            "QLabel { color: #000000; font-size: 14px; } QPushButton { color: #000000; padding: 6px 12px; }")
        msg.exec()


class SchuelerTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Name, Klasse oder Jahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Klassen (Alle)", "MB", "MT", "KI", "WI"])
        self.filter_combo.setFixedWidth(180)
        self.filter_combo.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItems(["Schuljahre (Alle)", "2023-24", "2024-25", "2025-26", "2026-27"])
        self.filter_jahr.setFixedWidth(180)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_combo)
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        self.setup_table(6, ["ID", "Nachname", "Vorname", "Klasse", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_student_dialog)

        btn_import = QPushButton("📥 Schüler importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_students)

        btn_clean = QPushButton("🗑️ Archiv leeren")
        btn_clean.setStyleSheet(get_import_btn_style())
        btn_clean.clicked.connect(self.clean_archive)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        footer_layout.addWidget(btn_clean)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_back)
        self.main_layout.addLayout(footer_layout)

        self.search_input.textChanged.connect(self.refresh_data)
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        self.filter_jahr.currentTextChanged.connect(self.refresh_data)

        if self.db_manager:
            self.refresh_data()

    def refresh_data(self):
        if not self.db_manager: return
        search_text = self.search_input.text().lower()
        all_matching_students = self.db_manager.get_students()

        selected_klasse = self.filter_combo.currentText()
        selected_jahr = self.filter_jahr.currentText()

        filtered_students = []
        for s in all_matching_students:
            formatted_id = str(s[5])
            nachname = str(s[1]).lower()
            vorname = str(s[2]).lower()

            match_text = search_text in formatted_id.lower() or search_text in nachname or search_text in vorname
            match_klasse = (selected_klasse == "Klassen (Alle)" or s[3] == selected_klasse)
            match_jahr = (selected_jahr == "Schuljahre (Alle)" or s[4] == selected_jahr)

            if match_text and match_klasse and match_jahr:
                filtered_students.append(s)

        self.load_table_data(filtered_students)

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        # MUSTAFA DEMIRAL (Sprint 4): Transparente Hintergründe und Hover-Effekte für Mac-Kompatibilität in der Tabelle
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #E0E0E0; border-radius: 6px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
        """

        for row, student in enumerate(data_list):
            db_id = str(student[0])
            nachname = str(student[1])
            vorname = str(student[2])
            klasse = str(student[3])
            jahr = str(student[4])
            formatted_id = str(student[5])

            display_data = [formatted_id, nachname, vorname, klasse, jahr]
            full_name = f"{vorname} {nachname}"

            for col in range(5):
                item = QTableWidgetItem(display_data[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QBrush(Qt.GlobalColor.black))
                if col in [0, 3, 4]: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, sid=db_id: self.edit_student(sid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, sid=db_id, sname=full_name: self.delete_student(sid, sname))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            vorname = d.input_vorname.text().strip()
            nachname = d.input_nachname.text().strip()
            klasse = d.combo_klasse.currentText()
            jahr = d.combo_jahr.currentText()
            manual_id = d.input_id.text().strip()

            if self.db_manager:
                success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                if success:
                    self.refresh_data()
                    self.show_popup("Erfolg", f"Schüler {vorname} {nachname} wurde angelegt.")
                else:
                    self.show_popup("Fehler", f"Die ID {manual_id} ist in dieser Klasse bereits vergeben!")

    def edit_student(self, sid):
        if not self.db_manager: return
        current_data = self.db_manager.get_student_by_id(sid)
        if current_data:
            d = StudentDialog(self, student_data=current_data)
            if d.exec() == QDialog.DialogCode.Accepted:
                nachname = d.input_nachname.text().strip()
                vorname = d.input_vorname.text().strip()
                klasse = d.combo_klasse.currentText()
                jahr = d.combo_jahr.currentText()
                manual_id = d.input_id.text().strip()

                success = self.db_manager.update_student(sid, nachname, vorname, klasse, jahr, manual_id)
                if success:
                    self.refresh_data()
                else:
                    self.show_popup("Fehler", f"Die ID {manual_id} ist in dieser Klasse bereits vergeben!")

    # --- MUSTAFA DEMIRAL (Sprint 5): Die neue sichere Lösch-Logik (Soft- & Hard-Delete via Admin-Passwort) ---
    def delete_student(self, sid, student_name):
        if not self.db_manager: return

        dialog = StudentDeleteDialog(self, student_name=student_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.result_action == 'deactivate':
                self.db_manager.deactivate_student(sid)
                self.refresh_data()
                self.show_popup("Erfolg", f"Der Schüler '{student_name}' wurde sicher inaktiv gesetzt.")
            elif dialog.result_action == 'delete':
                self.db_manager.delete_student(sid)
                self.refresh_data()
                self.show_popup("Erfolg", f"Der Schüler '{student_name}' wurde endgültig gelöscht.")

    # --- MUSTAFA DEMIRAL (Sprint 5): Löscht nach Bestätigung alle Inaktiven restlos aus der DB ---
    def clean_archive(self):
        if not self.db_manager: return
        dialog = CleanArchiveDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            deleted_count = self.db_manager.delete_all_inactive_students()
            self.refresh_data()
            self.show_popup("Archiv geleert",
                            f"Erfolgreich ausgeführt!\n\nEs wurden {deleted_count} inaktive Schüler dauerhaft aus der Datenbank gelöscht.")

    # --- MUSTAFA DEMIRAL (Sprint 5): Intelligenter Import greift IDs ab und fängt Duplikate lautlos ab, ohne abzustürzen ---
    def import_students(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Schüler importieren", "",
                                                   "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)")
        if not file_path: return

        if not self.db_manager:
            self.show_popup("Fehler", "Keine Datenbankverbindung!")
            return

        try:
            imported_count = 0
            skipped_count = 0

            if file_path.lower().endswith('.csv'):
                with open(file_path, mode='r', encoding='utf-8-sig') as file:
                    header_line = file.readline()
                    delim = ';' if ';' in header_line else ','
                    file.seek(0)

                    reader = csv.reader(file, delimiter=delim)
                    headers = next(reader, [])

                    id_idx, vn_idx, nn_idx, kl_idx, j_idx = -1, -1, -1, -1, -1
                    for i, h in enumerate(headers):
                        h_up = str(h).upper()
                        if "ID" in h_up and id_idx == -1:
                            id_idx = i
                        elif "VORNAME" in h_up:
                            vn_idx = i
                        elif "NACHNAME" in h_up:
                            nn_idx = i
                        elif "KLASSE" in h_up:
                            kl_idx = i
                        elif "JAHR" in h_up:
                            j_idx = i

                    if vn_idx == -1 or nn_idx == -1:
                        id_idx, vn_idx, nn_idx, kl_idx, j_idx = 0, 1, 2, 3, 4

                    for row in reader:
                        if len(row) > max(vn_idx, nn_idx):
                            raw_id = str(row[id_idx]).strip() if id_idx != -1 and id_idx < len(row) else ""
                            vorname = str(row[vn_idx]).strip()
                            nachname = str(row[nn_idx]).strip()
                            klasse = str(row[kl_idx]).strip()
                            jahr = str(row[j_idx]).strip()

                            if not vorname or not nachname: continue
                            if klasse not in ["MB", "MT", "KI", "WI"]: continue

                            manual_id = None
                            if raw_id:
                                try:
                                    if '_' in raw_id:
                                        manual_id = int(raw_id.split('_')[-1])
                                    else:
                                        manual_id = int(raw_id)
                                except ValueError:
                                    pass

                            try:
                                success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                                if success:
                                    imported_count += 1
                                else:
                                    skipped_count += 1
                            except Exception:
                                skipped_count += 1

            elif file_path.lower().endswith('.xlsx'):
                try:
                    import pandas as pd
                except ImportError:
                    self.show_popup("Fehler",
                                    "Für den Excel-Import muss 'pandas' installiert sein!\nBitte führe 'pip install pandas openpyxl' im Terminal aus.")
                    return
                df = pd.read_excel(file_path)

                id_col = None
                for col in df.columns:
                    if "ID" in str(col).strip().upper():
                        id_col = col
                        break

                for index, row in df.iterrows():
                    try:
                        raw_id = ""
                        if id_col and pd.notna(row.get(id_col)):
                            raw_id = str(row.get(id_col)).strip()

                        vorname = str(row.get('Vorname', '')).strip()
                        nachname = str(row.get('Nachname', '')).strip()
                        klasse = str(row.get('Klasse', '')).strip()

                        jahr = str(row.get('Eintrittsschuljahr', '')).strip()
                        if not jahr or jahr == 'nan':
                            jahr = str(row.get('Schuljahr', '')).strip()

                        if nachname and vorname and nachname != 'nan':
                            if klasse not in ["MB", "MT", "KI", "WI"]: continue

                            manual_id = None
                            if raw_id and raw_id.lower() != 'nan':
                                try:
                                    if '_' in raw_id:
                                        manual_id = int(raw_id.split('_')[-1])
                                    else:
                                        manual_id = int(float(raw_id))
                                except ValueError:
                                    pass

                            success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                            if success:
                                imported_count += 1
                            else:
                                skipped_count += 1
                    except Exception:
                        skipped_count += 1

            self.refresh_data()
            self.show_popup("Import abgeschlossen",
                            f"Erfolgreich hinzugefügt: {imported_count}\nÜbersprungen (Fehler/Duplikate): {skipped_count}")

        except Exception as e:
            self.show_popup("Achtung", f"Der Import wurde abgebrochen:\n\n{e}")


class KlassenTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Klasse...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItem("Schuljahre (Alle)")
        self.refresh_year_filter()
        self.filter_jahr.setFixedWidth(200)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        self.setup_table(4, ["Schuljahr", "Klasse", "Anzahl Schüler", "Aktionen"])
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)

        self.search_input.textChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Klasse hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_klassen_dialog)

        btn_import = QPushButton("📥 Klassen importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_klassen)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_back)
        self.main_layout.addLayout(footer_layout)

        self.filter_table()

    def refresh_year_filter(self):
        if self.db_manager:
            try:
                jahre = self.db_manager.get_school_years()
                for j in jahre:
                    self.filter_jahr.addItem(str(j[1]))
            except Exception:
                pass

    def filter_table(self):
        if not self.db_manager: return
        alle_klassen = self.db_manager.get_classes()
        txt = self.search_input.text().lower()
        jahr_filter = self.filter_jahr.currentText()

        gefiltert = []
        for k in alle_klassen:
            s_jahr = str(k[0])
            s_name = str(k[1])
            match_txt = txt in s_name.lower() or txt in s_jahr.lower()
            match_jahr = (jahr_filter == "Schuljahre (Alle)" or jahr_filter == s_jahr)
            if match_txt and match_jahr:
                gefiltert.append(k)

        self.load_table_data(gefiltert)

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #E0E0E0; border-radius: 6px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
        """

        for row, klasse in enumerate(data_list):
            for col in range(3):
                item = QTableWidgetItem(str(klasse[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QBrush(Qt.GlobalColor.black))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            kid = f"{klasse[1]}_{klasse[0]}"
            kname = f"{klasse[1]} ({klasse[0]})"

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, id=kid: self.edit_klasse(id))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(30, 30)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, id=kid, name=kname: self.delete_klasse(id, name))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 3, action_widget)

    def open_klassen_dialog(self):
        d = KlassenDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            sj = d.combo_jahr.currentText()
            if name and sj != "Bitte wählen...":
                if self.db_manager.add_class(name, sj):
                    self.filter_table()
                else:
                    self.show_popup("Fehler", "Klasse konnte nicht gespeichert werden.")

    def edit_klasse(self, kid):
        self.show_popup("Info", f"Bearbeiten-Funktion für {kid} folgt in Kürze.")

    # --- MUSTAFA DEMIRAL (Sprint 5): Warnmeldung für die neue Kaskaden-Löschung angepasst ---
    def delete_klasse(self, kid, kname):
        parts = kid.split('_')
        if len(parts) < 2: return
        name, jahr = parts[0], parts[1]
        msg = f"⚠️ Möchten Sie die Klasse '{kname}' wirklich löschen?\n\nACHTUNG: Dadurch werden auch alle zugeordneten Schüler unwiderruflich entfernt!"

        if DeleteConfirmDialog(self, msg).exec() == QDialog.DialogCode.Accepted:
            try:
                self.db_manager.delete_class(name, jahr)
                self.filter_table()
                self.show_popup("Erfolg", f"Die Klasse '{kname}' samt Schülern wurde gelöscht.")
            except Exception as e:
                self.show_popup("Fehler", f"Löschen fehlgeschlagen: {e}")

    def import_klassen(self):
        self.show_popup("Info", "Import-Schnittstelle wird für MariaDB optimiert.")


class SchuljahrTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Schuljahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)
        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        self.main_layout.addLayout(action_layout)

        self.setup_table(3, ["ID", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)

        self.search_input.textChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schuljahr hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_jahr_dialog)

        btn_import = QPushButton("📥 Schuljahre importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_jahre)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_back)
        self.main_layout.addLayout(footer_layout)

        self.filter_table()

    def filter_table(self):
        if not self.db_manager: return
        txt = self.search_input.text().lower()
        alle_jahre = self.db_manager.get_school_years()
        gefiltert = [j for j in alle_jahre if txt in str(j[1]).lower()]
        self.load_table_data(gefiltert)

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
        """

        for row, jahr_row in enumerate(data_list):
            for col in range(2):
                item = QTableWidgetItem(str(jahr_row[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QBrush(Qt.GlobalColor.black))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_style)
            btn_delete.clicked.connect(lambda ch, jid=jahr_row[0], jname=str(jahr_row[1]): self.delete_jahr(jid, jname))

            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 2, action_widget)

    def open_jahr_dialog(self):
        d = SchuljahrDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            if name and self.db_manager:
                self.db_manager.add_school_year(name)
                self.filter_table()

    # --- MUSTAFA DEMIRAL (Sprint 5): Warnmeldung für die neue Kaskaden-Löschung angepasst ---
    def delete_jahr(self, jid, jahr_name):
        msg = f"⚠️ Möchten Sie das Schuljahr '{jahr_name}' wirklich löschen?\n\nACHTUNG: Dadurch werden auch ALLE Klassen und Schüler in diesem Jahr unwiderruflich entfernt!"
        if DeleteConfirmDialog(self, msg).exec() == QDialog.DialogCode.Accepted:
            try:
                self.db_manager.delete_school_year(jid)
                self.filter_table()
                self.show_popup("Erfolg", f"Das Schuljahr '{jahr_name}' samt Inhalt wurde gelöscht.")
            except Exception as e:
                self.show_popup("Fehler", f"Löschen fehlgeschlagen: {e}")

    def import_jahre(self):
        self.show_popup("Info", "Import-Funktion wird vorbereitet.")


# ==============================================================================
# CONTAINER
# ==============================================================================

class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)

        top_header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        top_header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 45, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = resource_path_any(os.path.join("pic", "technikerschule_logo.png"),
                                      os.path.join("..", "pic", "technikerschule_logo.png"))
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_header_layout.addWidget(logo_label)

        main_layout.addLayout(top_header_layout)

        sub_header_layout = QVBoxLayout()
        sub_header_layout.setSpacing(5)

        self.breadcrumb_label = QLabel("Startseite > Hauptmenü > Schülerverwaltung > Schüler")
        self.breadcrumb_label.setStyleSheet("color: #666666; font-style: italic;")

        self.page_title = QLabel("Schülerverwaltung")
        self.page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color: #F1BD4D;")

        sub_header_layout.addWidget(self.breadcrumb_label)
        sub_header_layout.addWidget(self.page_title)

        main_layout.addLayout(sub_header_layout)
        main_layout.addSpacing(15)

        self.tabs = QTabWidget()
        self.tabs.tabBar().setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)

        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #CCCCCC; 
                border-radius: 4px; 
                background-color: #FFFFFF; 
            }
            QTabBar::tab { 
                background-color: #F0F0F0; 
                color: #333333; 
                padding: 12px 0px; 
                font-weight: bold; 
                font-size: 15px; 
                border: 1px solid #CCCCCC;
                border-bottom: none; 
                border-top-left-radius: 6px; 
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background-color: #F1BD4D; 
                color: #FFFFFF; 
                border-color: #F1BD4D; 
            }
            QTabBar::tab:hover:!selected { 
                background-color: #E0E0E0; 
            }
        """)

        self.tab_schueler = SchuelerTab(self)
        self.tab_klassen = KlassenTab(self)
        self.tab_schuljahr = SchuljahrTab(self)

        self.tabs.addTab(self.tab_schueler, "👨‍🎓 Schüler")
        self.tabs.addTab(self.tab_klassen, "🏫 Klassen")
        self.tabs.addTab(self.tab_schuljahr, "📅 Schuljahre")

        self.tabs.currentChanged.connect(self.update_header_text)
        main_layout.addWidget(self.tabs)

        self.btn_back = QPushButton()
        self.btn_back.hide()
        self.tab_schueler.btn_back.clicked.connect(self.btn_back.click)
        self.tab_klassen.btn_back.clicked.connect(self.btn_back.click)
        self.tab_schuljahr.btn_back.clicked.connect(self.btn_back.click)

    # --- MUSTAFA DEMIRAL (Sprint 5): Automatisches Neu-Laden der Tabellen beim Tab-Wechsel ---
    def update_header_text(self, index):
        if index == 0:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schüler")
            self.page_title.setText("Schülerverwaltung")
            self.tab_schueler.refresh_data()
        elif index == 1:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schulklassen")
            self.page_title.setText("Schulklassenverwaltung")
            self.tab_klassen.refresh_year_filter()
            self.tab_klassen.filter_table()
        elif index == 2:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schuljahre")
            self.page_title.setText("Schuljahrverwaltung")
            self.tab_schuljahr.filter_table()
