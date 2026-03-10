# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: Gesamte Verwaltung (Schüler, Klassen, Schuljahre)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Stand: ID-Generierung gefixt, Breadcrumbs optimiert, Tabellen-Schrift schwarz
# ------------------------------------------------------------------------------

import os
import csv  # Luis Overrath: Import für die CSV-Verarbeitung
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,
    QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


# Hilfsfunktion für einheitliche Buttons (spart sehr viel Code für alle Module)
def get_btn_style(bg_color, text_color="white"):
    return f"""
    QPushButton {{ background-color: {bg_color}; color: {text_color}; padding: 8px 20px;
    border: 3px solid {bg_color}; border-radius: 6px; font-weight: bold; font-size: 14px; }}
    QPushButton:hover, QPushButton:focus {{ border: 3px solid #000000; }}
    QPushButton:pressed {{ background-color: #444444; border: 3px solid #000000; color: white; }}
    """


# Hilfsfunktion für den Import-Button (Weißer Hintergrund, grauer Rand)
def get_import_btn_style():
    return """
    QPushButton {
        background-color: #FFFFFF;
        color: #333333;
        padding: 8px 20px;
        border: 3px solid #E0E0E0;
        border-radius: 6px;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover, QPushButton:focus { border: 3px solid #000000; }
    QPushButton:pressed { background-color: #F0F0F0; border: 3px solid #000000; color: #333333; }
    """


# --- Ahmet: Bestätigungsdialog für das Löschen von Datensätzen (Zentral für alle) ---
class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None, warning_text="⚠️ Möchten Sie diesen Datensatz wirklich\nunwiderruflich löschen?"):
        super().__init__(parent)
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(400, 180)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel(warning_text)
        self.label.setFont(QFont("Open Sans", 11, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(self.label)

        # Auswahlbuttons (Abbrechen / Löschen)
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


# ==============================================================================
# DIALOGE FÜR DIE VERWALTUNG (Schüler, Klassen, Schuljahre)
# ==============================================================================

# --- Mustafa: Eingabemaske für Schüler-Daten ---
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

        # Eingabefelder
        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname eingeben")

        self.input_nachname = QLineEdit()
        self.input_nachname.setPlaceholderText("Nachname eingeben")

        self.combo_klasse = QComboBox()
        self.combo_klasse.addItems(["Bitte wählen...", "MB", "MT", "KI", "WI"])

        self.combo_jahr = QComboBox()
        self.combo_jahr.addItems(["Bitte wählen...", "2023-24", "2024-25", "2025-26", "2026-27"])

        for w in [self.input_vorname, self.input_nachname, self.combo_klasse, self.combo_jahr]:
            w.setFixedWidth(250)

        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        # Ahmet: Bestehende Daten laden, falls Bearbeitungsmodus
        if student_data:
            self.input_nachname.setText(student_data[1])
            self.input_vorname.setText(student_data[2])
            self.combo_klasse.setCurrentText(student_data[3])
            if len(student_data) > 4:
                self.combo_jahr.setCurrentText(student_data[4])

        form_layout.addRow(QLabel("Vorname*:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname*:"), self.input_nachname)
        form_layout.addRow(QLabel("Klasse*:"), self.combo_klasse)
        form_layout.addRow(QLabel("Schuljahr*:"), self.combo_jahr)

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


# --- Luis: Dialog für Klassenverwaltung ---
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


# --- Luis: Dialog für Schuljahrverwaltung ---
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
# BEREICH 2: REITER (TABS) INHALTE
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
        # Tabellen-Design mit erzwungener schwarzer Schrift
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                alternate-background-color: #F9F9F9;
                border: 1px solid #E0E0E0; 
                border-radius: 8px; 
                gridline-color: #EDEDED;
                color: #333333; 
                font-size: 14px;
            }
            QTableWidget::item {
                color: #333333;
            }
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


# --- Mustafa: Logik für den Schüler-Reiter ---
class SchuelerTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Filter
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach ID, Name oder Jahr...")
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

        # Tabelle
        self.setup_table(6, ["ID", "Nachname", "Vorname", "Klasse", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 140)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120)

        self.dummy_students = []
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_combo.currentTextChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        # Footer
        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_student_dialog)

        btn_import = QPushButton("📥 Schüler importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_students)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_back)
        self.main_layout.addLayout(footer_layout)

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        # Kleinere Aktionsbuttons (32x32, 16px Font)
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #E0E0E0; border-radius: 6px; }
            QPushButton:pressed { background-color: #CCCCCC; border-radius: 6px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
            QPushButton:pressed { background-color: #E57373; border-radius: 6px; }
        """

        for row, student in enumerate(data_list):
            for col in range(5):
                item = QTableWidgetItem(student[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if col in [0, 3, 4]: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet(f"background-color: {'#F9F9F9' if row % 2 != 0 else '#FFFFFF'};")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, sid=student[0]: self.edit_student(sid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, sid=student[0]: self.delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            kl = d.combo_klasse.currentText()
            sj = d.combo_jahr.currentText()

            # --- LUIS: GEFIXTE LOGIK FÜR DIE SCHÜLER-ID ---
            prefix = f"{kl}_{sj}_"
            # Suche alle bestehenden Nummern für genau diese Klasse und dieses Jahr
            existing_nums = [
                int(s[0].split('_')[-1])
                for s in self.dummy_students
                if s[0].startswith(prefix) and s[0].split('_')[-1].isdigit()
            ]
            # Nimm die höchste Nummer und rechne +1 (oder starte bei 1)
            next_num = max(existing_nums) + 1 if existing_nums else 1
            sid = f"{prefix}{next_num:03d}"

            self.dummy_students.append((sid, d.input_nachname.text().strip(), d.input_vorname.text().strip(), kl, sj))
            self.filter_table()

    def edit_student(self, sid):
        for i, s in enumerate(self.dummy_students):
            if s[0] == sid:
                d = StudentDialog(self, student_data=s)
                if d.exec() == QDialog.DialogCode.Accepted:
                    self.dummy_students[i] = (sid, d.input_nachname.text().strip(), d.input_vorname.text().strip(),
                                              d.combo_klasse.currentText(), d.combo_jahr.currentText())
                    self.filter_table()
                break

    def delete_student(self, sid):
        if DeleteConfirmDialog(self,
                               "⚠️ Möchten Sie diesen Schüler wirklich\nunwiderruflich löschen?").exec() == QDialog.DialogCode.Accepted:
            self.dummy_students = [s for s in self.dummy_students if s[0] != sid]
            self.filter_table()

    def filter_table(self):
        txt = self.search_input.text().lower()
        cls = self.filter_combo.currentText()
        jahr = self.filter_jahr.currentText()
        self.load_table_data([s for s in self.dummy_students if (
                    txt in s[0].lower() or txt in s[1].lower() or txt in s[2].lower() or txt in s[4].lower()) and (
                                          cls == "Klassen (Alle)" or cls == s[3]) and (
                                          jahr == "Schuljahre (Alle)" or jahr == s[4])])

    def import_students(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Schüler importieren", "",
                                                   "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)")
        if not file_path: return
        if file_path.lower().endswith('.xlsx'):
            self.show_popup("Hinweis", "Import wird in PBI7.2 implementiert.")
        elif file_path.lower().endswith('.csv'):
            try:
                imported_count = 0
                with open(file_path, mode='r', encoding='utf-8') as file:
                    for row in csv.reader(file, delimiter=';'):
                        if len(row) >= 5 and row[0] != "Schüler-ID":
                            sid, vor, nach, kl, j = [x.strip() for x in row[:5]]
                            if sid not in [s[0] for s in self.dummy_students]:
                                self.dummy_students.append((sid, nach, vor, kl, j))
                                imported_count += 1
                self.filter_table()
                self.show_popup("Erfolgreich",
                                f"CSV-Datei importiert!\n\nEs wurden {imported_count} Schüler hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Datei konnte nicht gelesen werden:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte .csv oder .xlsx wählen.")


# --- Luis: Logik für den Klassen-Reiter ---
class KlassenTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Filter
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Klasse...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItems(["Schuljahre (Alle)", "2023-24", "2024-25", "2025-26", "2026-27"])
        self.filter_jahr.setFixedWidth(200)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        # Tabelle
        self.setup_table(4, ["ID", "Klasse", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 120)

        self.dummy_klassen = []
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        # Footer
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

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        # Kleinere Aktionsbuttons (32x32, 16px Font)
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #E0E0E0; border-radius: 6px; }
            QPushButton:pressed { background-color: #CCCCCC; border-radius: 6px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
            QPushButton:pressed { background-color: #E57373; border-radius: 6px; }
        """

        for row, klasse in enumerate(data_list):
            for col in range(3):
                item = QTableWidgetItem(klasse[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if col != 1 else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet(f"background-color: {'#F9F9F9' if row % 2 != 0 else '#FFFFFF'};")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, kid=klasse[0]: self.edit_klasse(kid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, kid=klasse[0]: self.delete_klasse(kid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 3, action_widget)

    def open_klassen_dialog(self):
        d = KlassenDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            sj = d.combo_jahr.currentText()
            kid = f"{name}_{sj}"
            self.dummy_klassen.append((kid, name, sj))
            self.filter_table()

    def edit_klasse(self, kid):
        for i, k in enumerate(self.dummy_klassen):
            if k[0] == kid:
                d = KlassenDialog(self, klassen_data=k)
                if d.exec() == QDialog.DialogCode.Accepted:
                    self.dummy_klassen[i] = (kid, d.input_name.text().strip(), d.combo_jahr.currentText())
                    self.filter_table()
                break

    def delete_klasse(self, kid):
        if DeleteConfirmDialog(self,
                               "⚠️ Möchten Sie diese Klasse wirklich\nunwiderruflich löschen?").exec() == QDialog.DialogCode.Accepted:
            self.dummy_klassen = [k for k in self.dummy_klassen if k[0] != kid]
            self.filter_table()

    def filter_table(self):
        txt = self.search_input.text().lower()
        jahr = self.filter_jahr.currentText()
        self.load_table_data([k for k in self.dummy_klassen if (txt in k[0].lower() or txt in k[1].lower()) and (
                    jahr == "Schuljahre (Alle)" or jahr == k[2])])

    def import_klassen(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Klassen importieren", "",
                                                   "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)")
        if not file_path: return
        if file_path.lower().endswith('.xlsx'):
            self.show_popup("Hinweis", "Import wird in PBI7.2 implementiert.")
        elif file_path.lower().endswith('.csv'):
            try:
                imported_count = 0
                with open(file_path, mode='r', encoding='utf-8') as file:
                    for row in csv.reader(file, delimiter=';'):
                        if len(row) >= 2 and row[0] != "Klasse":
                            name, jahr = row[0].strip(), row[1].strip()
                            if name and jahr and not any(k[1] == name and k[2] == jahr for k in self.dummy_klassen):
                                kid = f"{name}_{jahr}"
                                self.dummy_klassen.append((kid, name, jahr))
                                imported_count += 1
                self.filter_table()
                self.show_popup("Erfolgreich",
                                f"CSV-Datei importiert!\n\nEs wurden {imported_count} Klassen hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Fehler beim Import:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte eine .csv oder .xlsx auswählen.")


# --- Luis: Logik für den Schuljahr-Reiter ---
class SchuljahrTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Filter
        action_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Schuljahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)
        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        self.main_layout.addLayout(action_layout)

        # Tabelle
        self.setup_table(3, ["ID", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)

        self.dummy_jahre = []
        self.search_input.textChanged.connect(self.filter_table)

        # Footer
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

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        # Kleinere Aktionsbuttons (32x32, 16px Font)
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #E0E0E0; border-radius: 6px; }
            QPushButton:pressed { background-color: #CCCCCC; border-radius: 6px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 16px; color: #333333; }
            QPushButton:hover { background-color: #FFCDD2; border-radius: 6px; }
            QPushButton:pressed { background-color: #E57373; border-radius: 6px; }
        """

        for row, jahr in enumerate(data_list):
            for col in range(2):
                item = QTableWidgetItem(jahr[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if col == 0 else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet(f"background-color: {'#F9F9F9' if row % 2 != 0 else '#FFFFFF'};")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, jid=jahr[0]: self.edit_jahr(jid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, jid=jahr[0]: self.delete_jahr(jid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 2, action_widget)

    def open_jahr_dialog(self):
        d = SchuljahrDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            jid = name
            if not any(j[0] == jid for j in self.dummy_jahre):
                self.dummy_jahre.append((jid, name))
                self.filter_table()
            else:
                self.show_popup("Fehler", "Dieses Schuljahr existiert bereits.")

    def edit_jahr(self, jid):
        for i, j in enumerate(self.dummy_jahre):
            if j[0] == jid:
                d = SchuljahrDialog(self, jahr_data=j)
                if d.exec() == QDialog.DialogCode.Accepted:
                    self.dummy_jahre[i] = (jid, d.input_name.text().strip())
                    self.filter_table()
                break

    def delete_jahr(self, jid):
        if DeleteConfirmDialog(self,
                               "⚠️ Möchten Sie dieses Schuljahr wirklich\nunwiderruflich löschen?").exec() == QDialog.DialogCode.Accepted:
            self.dummy_jahre = [j for j in self.dummy_jahre if j[0] != jid]
            self.filter_table()

    def filter_table(self):
        txt = self.search_input.text().lower()
        self.load_table_data([j for j in self.dummy_jahre if txt in j[0].lower() or txt in j[1].lower()])

    def import_jahre(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Schuljahre importieren", "",
                                                   "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)")
        if not file_path: return
        if file_path.lower().endswith('.xlsx'):
            self.show_popup("Hinweis", "Import wird in PBI7.2 implementiert.")
        elif file_path.lower().endswith('.csv'):
            try:
                imported_count = 0
                with open(file_path, mode='r', encoding='utf-8') as file:
                    for row in csv.reader(file, delimiter=';'):
                        if row and row[0] != "Schuljahr":
                            name = row[0].strip()
                            if name and not any(j[1] == name for j in self.dummy_jahre):
                                jid = name
                                self.dummy_jahre.append((jid, name))
                                imported_count += 1
                self.filter_table()
                self.show_popup("Erfolgreich",
                                f"CSV-Datei importiert!\n\nEs wurden {imported_count} Schuljahre hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Fehler beim Import:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte eine .csv oder .xlsx auswählen.")


# ==============================================================================
# BEREICH 3: DAS HAUPT-WIDGET (Container)
# ==============================================================================

# WICHTIG: Die Klasse muss SchuelerverwaltungWidget heißen,
# damit MainWindow.py sie per Import findet!
class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)

        # Header Bereich
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 45, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")

        # Dynamisches Breadcrumb
        self.breadcrumb_label = QLabel("Startseite > Hauptmenü > Schülerverwaltung > Schüler")
        self.breadcrumb_label.setStyleSheet("color: #666666; font-style: italic;")

        # Dynamischer Seiten-Titel
        self.page_title = QLabel("Schülerverwaltung")
        self.page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color: #F1BD4D;")

        title_container.addWidget(title_label)
        title_container.addWidget(self.breadcrumb_label)
        title_container.addWidget(self.page_title)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        logo_label = QLabel()
        # Pfad zum Logo ggf. anpassen
        pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "..", "pic", "technikerschule_logo.png"))
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        header_layout.addWidget(logo_label)
        main_layout.addLayout(header_layout)

        main_layout.addSpacing(15)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.tabBar().setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #CCCCCC; border-radius: 4px; background: white; }
            QTabBar { qproperty-expanding: 1; }
            QTabBar::tab { 
                background: #F0F0F0; 
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
                background: #F1BD4D; 
                color: white; 
                border-color: #F1BD4D;
            }
            QTabBar::tab:hover:!selected { background: #E0E0E0; }
        """)

        self.tab_schueler = SchuelerTab()
        self.tab_klassen = KlassenTab()
        self.tab_schuljahr = SchuljahrTab()

        self.tabs.addTab(self.tab_schueler, "👨‍🎓 Schüler")
        self.tabs.addTab(self.tab_klassen, "🏫 Klassen")
        self.tabs.addTab(self.tab_schuljahr, "📅 Schuljahre")

        self.tabs.currentChanged.connect(self.update_header_text)

        main_layout.addWidget(self.tabs)

        # UNSICHTBARER DUMMY-BUTTON für die MainWindow.py Verknüpfung
        # MainWindow.py erwartet einen Button namens 'btn_back' direkt im Widget
        self.btn_back = QPushButton()
        self.btn_back.hide()

        # Alle internen Zurück-Buttons lösen den Haupt-Zurück-Button aus
        self.tab_schueler.btn_back.clicked.connect(self.btn_back.click)
        self.tab_klassen.btn_back.clicked.connect(self.btn_back.click)
        self.tab_schuljahr.btn_back.clicked.connect(self.btn_back.click)

    def update_header_text(self, index):
        """Aktualisiert Breadcrumb und Titel je nach ausgewähltem Tab"""
        if index == 0:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schüler")
            self.page_title.setText("Schülerverwaltung")
        elif index == 1:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schulklassen")
            self.page_title.setText("Schulklassenverwaltung")
        elif index == 2:
            self.breadcrumb_label.setText("Startseite > Hauptmenü > Schülerverwaltung > Schuljahre")
            self.page_title.setText("Schuljahrverwaltung")