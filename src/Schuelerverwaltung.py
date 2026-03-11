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
from database_manager import DatabaseManager


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


# --- Mustafa, René: Logik für den Schüler-Reiter ---
class SchuelerTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.db_manager = DatabaseManager()

        # UI-Setup (Filter Layout)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach ID, Name oder Klasse...")
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

        # Tabelle initialisieren
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

        self.search_input.textChanged.connect(self.refresh_data)
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        self.filter_jahr.currentTextChanged.connect(self.refresh_data)

        self.refresh_data()

    def refresh_data(self):
        search_text = self.search_input.text()
        all_matching_students = self.db_manager.get_students(search_text)

        selected_klasse = self.filter_combo.currentText()
        selected_jahr = self.filter_jahr.currentText()

        filtered_students = [
            s for s in all_matching_students
            if (selected_klasse == "Klassen (Alle)" or s[3] == selected_klasse) and
               (selected_jahr == "Schuljahre (Alle)" or s[4] == selected_jahr)
        ]

        self.load_table_data(filtered_students)

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

        for row, student in enumerate(data_list):
            # student = (ID, Nachname, Vorname, Klasse, Jahr)
            for col in range(5):
                item = QTableWidgetItem(str(student[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if col in [0, 3, 4]: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            # Bearbeiten-Logik (muss noch auf DB umgestellt werden)
            btn_edit.clicked.connect(lambda ch, sid=student[0]: self.edit_student(sid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            # Löschen direkt in der MariaDB
            btn_delete.clicked.connect(lambda ch, sid=student[0]: self.delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    #Use Db Data from now on instead of dummy data, but keep the dummy data for testing purposes
    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            vorname = d.input_vorname.text().strip()
            nachname = d.input_nachname.text().strip()
            klasse = d.combo_klasse.currentText()
            jahr = d.combo_jahr.currentText()

            self.db_manager.add_student(nachname, vorname, klasse, jahr)

            self.refresh_data()
            self.show_popup("Erfolg", f"Schüler {vorname} {nachname} wurde angelegt.")

    def edit_student(self, sid):
        current_data = self.db_manager.get_student_by_id(sid)

        if current_data:
            d = StudentDialog(self, student_data=current_data)
            if d.exec() == QDialog.DialogCode.Accepted:
                nachname = d.input_nachname.text().strip()
                vorname = d.input_vorname.text().strip()
                klasse = d.combo_klasse.currentText()
                jahr = d.combo_jahr.currentText()

                self.db_manager.update_student(sid, nachname, vorname, klasse, jahr)
                self.refresh_data()

    def delete_student(self, sid):
        if DeleteConfirmDialog(self,
                               "⚠️ Möchten Sie diesen Schüler wirklich löschen?").exec() == QDialog.DialogCode.Accepted:
            self.db_manager.delete_student(sid)
            self.refresh_data()

    def import_students(self):
        """Liest eine CSV und schreibt jeden Schüler einzeln in die MariaDB."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Schüler importieren", "", "CSV-Dateien (*.csv)")
        if not file_path:
            return

        try:
            imported_count = 0
            with open(file_path, mode='r', encoding='utf-8') as file:
                # Trenner ist laut deinem Code ';', Header wird übersprungen
                reader = csv.reader(file, delimiter=';')
                for row in reader:
                    if len(row) >= 4 and row[0] != "Nachname":
                        # Annahme: CSV Spalten = Nachname; Vorname; Klasse; Schuljahr
                        nachname, vorname, klasse, jahr = [x.strip() for x in row[:4]]

                        self.db_manager.add_student(nachname, vorname, klasse, jahr)
                        imported_count += 1

            self.refresh_data()
            self.show_popup("Import fertig", f"{imported_count} Schüler wurden in die Datenbank geladen.")

        except Exception as e:
            self.show_popup("Fehler", f"CSV-Import fehlgeschlagen:\n{e}")


# --- Luis,René: Logik für den Klassen-Reiter ---
class KlassenTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Zugriff auf den zentralen DatabaseManager vom MainWindow
        self.db_manager = parent.db_manager if parent else None

        # --- FILTER-BEREICH (OBEN) ---
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Klasse...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItem("Schuljahre (Alle)")
        # Lädt die Jahre direkt beim Start aus der DB
        self.refresh_year_filter()

        self.filter_jahr.setFixedWidth(200)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        # --- TABELLEN-KONFIGURATION ---
        # Spalten: Schuljahr, Klasse, Anzahl Schüler, Aktionen
        self.setup_table(4, ["Schuljahr", "Klasse", "Anzahl Schüler", "Aktionen"])
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)

        # Event-Handler für Filter-Änderungen
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        # --- FOOTER (UNTEN) ---
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

        # Daten beim ersten Öffnen laden
        self.filter_table()

    def refresh_year_filter(self):
        """Befüllt das Dropdown-Menü mit den Schuljahren aus der Datenbank."""
        if self.db_manager:
            try:
                jahre = self.db_manager.get_school_years()
                for j in jahre:
                    # j[1] entspricht der Spalte 'jahr' (z.B. '25/26')
                    self.filter_jahr.addItem(str(j[1]))
            except Exception as e:
                print(f"Fehler beim Laden der Schuljahre: {e}")

    def filter_table(self):
        """Holt Daten aus der View und wendet die UI-Filter an."""
        if not self.db_manager:
            return

        # View liefert: (schuljahr, schulklasse, anzahl_schueler)
        alle_klassen = self.db_manager.get_classes()

        txt = self.search_input.text().lower()
        jahr_filter = self.filter_jahr.currentText()

        gefiltert = []
        for k in alle_klassen:
            s_jahr = str(k[0])
            s_name = str(k[1])

            # Textsuche in Name ODER Jahr
            match_txt = txt in s_name.lower() or txt in s_jahr.lower()
            # Filter nach Jahr (oder Alle)
            match_jahr = (jahr_filter == "Schuljahre (Alle)" or jahr_filter == s_jahr)

            if match_txt and match_jahr:
                gefiltert.append(k)

        self.load_table_data(gefiltert)

    def load_table_data(self, data_list):
        """Befüllt das TableWidget und erstellt die Aktions-Buttons."""
        self.table.setRowCount(len(data_list))

        btn_style = "QPushButton { background: transparent; border: none; font-size: 16px; }"

        for row, klasse in enumerate(data_list):
            # Daten-Zellen befüllen (Jahr, Klasse, Anzahl)
            for col in range(3):
                item = QTableWidgetItem(str(klasse[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Nur Lesen
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            # Container für Buttons (✏️ und 🗑️)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)

            # Eindeutiger Identifier für die Callbacks (Name_Jahr)
            kid = f"{klasse[1]}_{klasse[0]}"

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setStyleSheet(btn_style)
            btn_edit.clicked.connect(lambda ch, id=kid: self.edit_klasse(id))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(30, 30)
            btn_delete.setStyleSheet(btn_style)
            btn_delete.clicked.connect(lambda ch, id=kid: self.delete_klasse(id))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 3, action_widget)

    def open_klassen_dialog(self):
        """Öffnet den Dialog zum Hinzufügen einer neuen Klasse in die DB."""
        d = KlassenDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            sj = d.combo_jahr.currentText()
            if name and sj != "Bitte wählen...":
                # Datenbank-Aufruf
                if self.db_manager.add_class(name, sj):
                    self.filter_table()  # Tabelle aktualisieren
                else:
                    self.show_popup("Fehler", "Klasse konnte nicht gespeichert werden.")

    def edit_klasse(self, kid):
        """Platzhalter für die Bearbeitungs-Logik (Update)."""
        self.show_popup("Info", f"Bearbeiten-Funktion für {kid} folgt in Kürze.")

    def delete_klasse(self, kid):
        """Löscht die Klasse aus der Datenbank."""
        parts = kid.split('_')
        if len(parts) < 2: return

        name, jahr = parts[0], parts[1]
        msg = f"⚠️ Möchten Sie die Klasse '{name}' ({jahr}) wirklich löschen?\n\nDadurch werden auch alle zugeordneten Schüler entfernt!"

        if DeleteConfirmDialog(self, msg).exec() == QDialog.DialogCode.Accepted:
            try:
                self.db_manager.delete_class(name, jahr)
                self.filter_table()  # Refresh
            except Exception as e:
                self.show_popup("Fehler", f"Löschen fehlgeschlagen: {e}")

    def import_klassen(self):
        """Anbindung an CSV-Import."""
        self.show_popup("Info", "Import-Schnittstelle wird für MariaDB optimiert.")


# --- Luis: Logik für den Schuljahr-Reiter ---
class SchuljahrTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        # WICHTIG: Den db_manager vom parent holen
        self.db_manager = parent.db_manager if parent else None

        # Filter-Bereich
        action_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Schuljahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)
        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        self.main_layout.addLayout(action_layout)

        # Tabelle Setup
        self.setup_table(3, ["ID", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)

        self.search_input.textChanged.connect(self.filter_table)

        # Footer
        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schuljahr hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))

        # HIER war der Fehler: Die Methode muss existieren!
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

        # Daten initial laden
        self.filter_table()

    def filter_table(self):
        """Holt Daten aus der DB und filtert sie."""
        if not self.db_manager:
            return
        txt = self.search_input.text().lower()
        alle_jahre = self.db_manager.get_school_years()
        gefiltert = [j for j in alle_jahre if txt in str(j[1]).lower()]
        self.load_table_data(gefiltert)

    def load_table_data(self, data_list):
        """Befüllt die UI Tabelle."""
        self.table.setRowCount(len(data_list))
        btn_style = "QPushButton { background: transparent; border: none; font-size: 16px; }"

        for row, jahr_row in enumerate(data_list):
            for col in range(2):
                item = QTableWidgetItem(str(jahr_row[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_style)
            btn_delete.clicked.connect(lambda ch, jid=jahr_row[0]: self.delete_jahr(jid))

            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 2, action_widget)

    def open_jahr_dialog(self):
        """Öffnet den Dialog und speichert in die DB."""
        # Falls SchuljahrDialog in einer anderen Datei liegt: from dialogs import SchuljahrDialog
        d = SchuljahrDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            if name and self.db_manager:
                self.db_manager.add_school_year(name)
                self.filter_table()

    def delete_jahr(self, jid):
        """Löscht ein Jahr aus der Datenbank."""
        if DeleteConfirmDialog(self, "⚠️ Schuljahr wirklich löschen?").exec() == QDialog.DialogCode.Accepted:
            try:
                conn = self.db_manager._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM Schuljahr WHERE schuljahr_id = %s", (jid,))
                conn.close()
                self.filter_table()
            except Exception as e:
                self.show_popup("Fehler", "Löschen nicht möglich (Klassen vorhanden).")

    def import_jahre(self):
        self.show_popup("Info", "Import-Funktion wird vorbereitet.")

# ==============================================================================
# BEREICH 3: DAS HAUPT-WIDGET (Container)
# ==============================================================================

# WICHTIG: Die Klasse muss SchuelerverwaltungWidget heißen,
# damit MainWindow.py sie per Import findet!
class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None
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

        self.tab_schueler = SchuelerTab(self)
        self.tab_klassen = KlassenTab(self)
        self.tab_schuljahr = SchuljahrTab(self)

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