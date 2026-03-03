# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: Gesamte Verwaltung (Schüler, Klassen, Schuljahre)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Stand: Alle 3 PBIs (3.3.3, 3.3.1, 3.3.2) in einer Datei zusammengefasst
# ------------------------------------------------------------------------------
import os
import csv  # Luis Overrath: Import für die CSV-Verarbeitung
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
                             QFileDialog, QMessageBox)  # Mustafa Demiral: QMessageBox hinzugefügt
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


# --- Mustafa: Eingabemaske für neue Schüler oder zum Bearbeiten ---
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
            if len(student_data) > 4: self.combo_jahr.setCurrentText(student_data[4])

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

    # Validierung komprimiert
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


# --- Mustafa: Haupt-Widget der Schülerverwaltung ---
class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

        # Header: Schullogo und Projektname
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
        pixmap = QPixmap(self.get_image_path("technikerschule_logo.png"))
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)

        # Navigation & Titel
        self.back_label = QLabel("Startseite > Hauptmenü > Schülerverwaltung")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        page_title = QLabel("Schülerverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #F1BD4D; margin-left: 10px;")
        main_layout.addWidget(page_title)

        # Filter-Leiste
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)
        action_layout.setSpacing(20)

        input_style = """
            QWidget { padding: 12px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px; }
            QWidget:focus { border: 2px solid #000000; } 
        """

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach ID, Name oder Jahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(input_style)
        action_layout.addWidget(self.search_input)

        action_layout.addStretch()  # Mustafa Demiral: Schiebt die Filter nach rechts

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Klassen (Alle)", "MB", "MT", "KI", "WI"])
        self.filter_combo.setFixedWidth(180)
        self.filter_combo.setStyleSheet(input_style)
        action_layout.addWidget(self.filter_combo)

        # Mustafa Demiral: Zweites Dropdown für den Schuljahr-Filter
        self.filter_jahr = QComboBox()
        self.filter_jahr.addItems(["Schuljahre (Alle)", "2023-24", "2024-25", "2025-26", "2026-27"])
        self.filter_jahr.setFixedWidth(180)
        self.filter_jahr.setStyleSheet(input_style)
        action_layout.addWidget(self.filter_jahr)

        main_layout.addLayout(action_layout)

        # Mustafa: Definition der Haupttabelle
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Nachname", "Vorname", "Klasse", "Schuljahr", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; alternate-background-color: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; font-size: 15px; color: #333333; gridline-color: #EDEDED; }
            QHeaderView::section { background-color: #F0F0F0; color: #000000; font-weight: bold; border: none; border-bottom: 3px solid #F1BD4D; padding: 12px; }
        """)
        self.table.verticalHeader().setVisible(False)

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
        self.table.setColumnWidth(5, 150)
        main_layout.addWidget(self.table)

        # Ahmet: Initialisierung der Dummy-Daten für die Entwicklung
        self.dummy_students = []

        self.load_table_data(self.dummy_students)
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_combo.currentTextChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        # --- FOOTER BEREICH ---
        footer_layout = QHBoxLayout()

        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_student_dialog)
        footer_layout.addWidget(btn_add)

        footer_layout.addStretch()  # Mustafa Demiral: Zentrierungshilfe

        # Mustafa Demiral: Excel-Import Button (Mitte, Platzhalter für PBI 3.3.3)
        btn_import = QPushButton("📥 Schüler importieren")
        btn_import.setStyleSheet("""
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
        """)
        btn_import.clicked.connect(self.import_students)
        footer_layout.addWidget(btn_import)

        footer_layout.addStretch()  # Mustafa Demiral: Zentrierungshilfe

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(get_btn_style("#F1BD4D"))
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        # Originaler Style für die Tabellen-Aktionsbuttons (Grau für Edit, Rot für Delete)
        btn_edit_style = """
            QPushButton { background: transparent; border: none; font-size: 20px; }
            QPushButton:hover, QPushButton:pressed { background-color: #E0E0E0; border-radius: 8px; }
        """
        btn_delete_style = """
            QPushButton { background: transparent; border: none; font-size: 20px; }
            QPushButton:hover, QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }
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
            btn_edit.setFixedSize(45, 45)
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(45, 45)

            btn_edit.setStyleSheet(btn_edit_style)
            btn_delete.setStyleSheet(btn_delete_style)

            btn_edit.clicked.connect(lambda ch, sid=student[0]: self.edit_student(sid))
            btn_delete.clicked.connect(lambda ch, sid=student[0]: self.delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    # Mustafa: Öffnet den Dialog zum Hinzufügen eines neuen Schülers
    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            klasse, jahr = d.combo_klasse.currentText(), d.combo_jahr.currentText()

            # Luis Overrath: Automatische Generierung der Schüler-ID (Klasse_Jahr_Laufnummer)
            prefix = f"{klasse}_{jahr}_"
            max_num = max([int(s[0].split('_')[-1]) for s in self.dummy_students if s[0].startswith(prefix)] + [0])

            self.dummy_students.append(
                (f"{prefix}{max_num + 1:03d}", d.input_nachname.text().strip(), d.input_vorname.text().strip(), klasse,
                 jahr))
            self.dummy_students.sort(key=lambda x: x[0])
            self.filter_table()

    def edit_student(self, sid):
        for i, s in enumerate(self.dummy_students):
            if s[0] == sid:
                d = StudentDialog(self, student_data=s)
                if d.exec() == QDialog.DialogCode.Accepted:
                    self.dummy_students[i] = (sid, d.input_nachname.text().strip(), d.input_vorname.text().strip(),
                                              d.combo_klasse.currentText(), d.combo_jahr.currentText())
                    self.dummy_students.sort(key=lambda x: x[0])
                    self.filter_table()
                break

    def delete_student(self, sid):
        if DeleteConfirmDialog(self,
                               "⚠️ Möchten Sie diesen Schüler wirklich\nunwiderruflich löschen?").exec() == QDialog.DialogCode.Accepted:
            self.dummy_students = [s for s in self.dummy_students if s[0] != sid]
            self.filter_table()

    # Ahmet: Such- und Filterlogik für die Tabellenanzeige
    def filter_table(self):
        txt, cls, jahr = self.search_input.text().lower(), self.filter_combo.currentText(), self.filter_jahr.currentText()
        self.load_table_data([s for s in self.dummy_students if
                              (txt in s[0].lower() or txt in s[1].lower() or txt in s[2].lower() or txt in s[
                                  4].lower()) and
                              (cls == "Klassen (Alle)" or cls == s[3]) and
                              (jahr == "Schuljahre (Alle)" or jahr == s[4])])

    def show_popup(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(
            "QLabel { color: #000000; font-size: 14px; } QPushButton { color: #000000; padding: 6px 12px; }")
        msg.exec()

    # Mustafa Demiral: Dialog zur Dateiauswahl für den Datei-Import (PBI 3.3.3)
    def import_students(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Schüler importieren", "",
                                                   "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)")
        if not file_path: return

        if file_path.lower().endswith('.xlsx'):
            self.show_popup("Hinweis",
                            "Import wird in PBI7.2 implementiert.\n\n(Tipp: Für einen echten Test-Import nutze bitte die .csv Datei).")
        elif file_path.lower().endswith('.csv'):
            try:
                if os.path.getsize(file_path) == 0:
                    return self.show_popup("Fehler", "Die ausgewählte Datei ist leer.")

                # Luis Overrath: Einlesen der CSV-Datei und Aktualisieren der Datenliste
                imported_count = 0
                with open(file_path, mode='r', encoding='utf-8') as file:
                    for row in csv.reader(file, delimiter=';'):
                        # Luis Overrath: Angepasst an die Spalten der Testdaten (ID, Vorname, Nachname, Klasse, Schuljahr)
                        if len(row) >= 5 and row[0] != "Schüler-ID":
                            sid, vor, nach, kl, j = [x.strip() for x in row[:5]]
                            if sid not in [s[0] for s in self.dummy_students]:
                                self.dummy_students.append((sid, nach, vor, kl, j))
                                imported_count += 1

                # Mustafa Demiral: Automatische Sortierung der Liste nach ID
                self.dummy_students.sort(key=lambda x: x[0])
                self.filter_table()

                # Mustafa Demiral: Erfolgsmeldung nach erfolgreichem Import (Schriftfarbe Schwarz)
                self.show_popup("Erfolgreich",
                                f"CSV-Datei erfolgreich importiert!\n\nEs wurden {imported_count} neue Schüler hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Datei konnte nicht gelesen werden:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte eine gültige Excel (.xlsx) oder CSV (.csv) Datei auswählen.")


# ==============================================================================
# BEREICH 2: KLASSENVERWALTUNG (PBI 3.3.1)
# ==============================================================================

# --- Mustafa: Eingabemaske für neue Klassen oder zum Bearbeiten ---
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
        self.input_name.setPlaceholderText("z.B. MB oder 10A")

        self.combo_jahr = QComboBox()
        self.combo_jahr.addItems(["Bitte wählen...", "2023-24", "2024-25", "2025-26", "2026-27"])

        for w in [self.input_name, self.combo_jahr]:
            w.setFixedWidth(250)

        self.error_label = QLabel("Bitte alle Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        # Ahmet: Bestehende Daten laden
        if klassen_data:
            self.input_name.setText(klassen_data[1])
            self.combo_jahr.setCurrentText(klassen_data[2])

        form_layout.addRow(QLabel("Klassenname*:"), self.input_name)
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

        valid &= check_field(self.input_name, not self.input_name.text().strip())
        valid &= check_field(self.combo_jahr, self.combo_jahr.currentText() == "Bitte wählen...")

        if not valid:
            self.error_label.show()
        else:
            self.accept()


# --- Mustafa & Luis: Haupt-Widget der Klassenverwaltung ---
class KlassenverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

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
        pixmap = QPixmap(self.get_image_path("technikerschule_logo.png"))
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)
        main_layout.addLayout(header_layout)

        self.back_label = QLabel("Startseite > Hauptmenü > Schulklassen")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        page_title = QLabel("Schulklassenverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #F1BD4D; margin-left: 10px;")
        main_layout.addWidget(page_title)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)
        action_layout.setSpacing(20)

        input_style = "padding: 12px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        focus_style = "QWidget:focus { border: 2px solid #000000; }"

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Klasse...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(input_style + focus_style)
        action_layout.addWidget(self.search_input)

        action_layout.addStretch()

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItems(["Schuljahre (Alle)", "2023-24", "2024-25", "2025-26", "2026-27"])
        self.filter_jahr.setFixedWidth(200)
        self.filter_jahr.setStyleSheet(input_style + focus_style)
        action_layout.addWidget(self.filter_jahr)

        main_layout.addLayout(action_layout)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Klasse", "Schuljahr", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; alternate-background-color: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; font-size: 15px; color: #333333; gridline-color: #EDEDED; }
            QHeaderView::section { background-color: #F0F0F0; color: #000000; font-weight: bold; border: none; border-bottom: 3px solid #F1BD4D; padding: 12px; }
        """)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 150)
        main_layout.addWidget(self.table)

        self.dummy_klassen = []

        self.load_table_data(self.dummy_klassen)
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Klasse hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_klassen_dialog)
        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()

        btn_import = QPushButton("📥 Klassen importieren")
        btn_import.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #333333; padding: 8px 20px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 14px; }
            QPushButton:hover, QPushButton:focus { border: 3px solid #000000; }
            QPushButton:pressed { background-color: #F0F0F0; border: 3px solid #000000; color: #333333; }
        """)
        btn_import.clicked.connect(self.import_klassen)
        footer_layout.addWidget(btn_import)
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(get_btn_style("#F1BD4D"))
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    def show_popup(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(
            "QLabel { color: #000000; font-size: 14px; } QPushButton { color: #000000; padding: 6px 12px; }")
        msg.exec()

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_edit_style = "QPushButton { background: transparent; border: none; font-size: 20px; } QPushButton:hover, QPushButton:pressed { background-color: #E0E0E0; border-radius: 8px; }"
        btn_delete_style = "QPushButton { background: transparent; border: none; font-size: 20px; } QPushButton:hover, QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }"

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
            btn_edit.setFixedSize(45, 45)
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(45, 45)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_delete.setStyleSheet(btn_delete_style)

            btn_edit.clicked.connect(lambda ch, kid=klasse[0]: self.edit_klasse(kid))
            btn_delete.clicked.connect(lambda ch, kid=klasse[0]: self.delete_klasse(kid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 3, action_widget)

    def open_klassen_dialog(self):
        d = KlassenDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name, jahr = d.input_name.text().strip(), d.combo_jahr.currentText()
            max_num = max([int(k[0].split('_')[-1]) for k in self.dummy_klassen if k[0].startswith("KL_")] + [0])
            self.dummy_klassen.append((f"KL_{max_num + 1:03d}", name, jahr))
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
        txt, jahr = self.search_input.text().lower(), self.filter_jahr.currentText()
        self.load_table_data([k for k in self.dummy_klassen if
                              (txt in k[0].lower() or txt in k[1].lower()) and
                              (jahr == "Schuljahre (Alle)" or jahr == k[2])])

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
                            if name and jahr:
                                if not any(k[1] == name and k[2] == jahr for k in self.dummy_klassen):
                                    max_num = max([int(k[0].split('_')[-1]) for k in self.dummy_klassen if
                                                   k[0].startswith("KL_")] + [0])
                                    self.dummy_klassen.append((f"KL_{max_num + 1:03d}", name, jahr))
                                    imported_count += 1
                self.filter_table()
                self.show_popup("Erfolgreich",
                                f"CSV-Datei importiert!\n\nEs wurden {imported_count} Klassen hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Fehler beim Import:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte eine .csv oder .xlsx auswählen.")


# ==============================================================================
# BEREICH 3: SCHULJAHRVERWALTUNG (PBI 3.3.2)
# ==============================================================================

# --- Mustafa: Eingabemaske für neue Schuljahre oder zum Bearbeiten ---
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
        form_layout.setSpacing(15)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. 2024-25")
        self.input_name.setFixedWidth(250)

        self.error_label = QLabel("Bitte den Namen des Schuljahres eingeben.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        # Ahmet: Bestehende Daten laden
        if jahr_data:
            self.input_name.setText(jahr_data[1])

        form_layout.addRow(QLabel("Schuljahr*:"), self.input_name)
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
        if not self.input_name.text().strip():
            self.input_name.setStyleSheet("border: 2px solid #D32F2F")
            self.error_label.show()
        else:
            self.input_name.setStyleSheet("")
            self.accept()


# --- Mustafa & Luis: Haupt-Widget der Schuljahrverwaltung ---
class SchuljahrverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

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
        pixmap = QPixmap(self.get_image_path("technikerschule_logo.png"))
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)
        main_layout.addLayout(header_layout)

        self.back_label = QLabel("Startseite > Hauptmenü > Schuljahre")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        page_title = QLabel("Schuljahrverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #F1BD4D; margin-left: 10px;")
        main_layout.addWidget(page_title)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Schuljahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(
            "padding: 12px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;")
        action_layout.addWidget(self.search_input)
        action_layout.addStretch()

        main_layout.addLayout(action_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Schuljahr", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; alternate-background-color: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; font-size: 15px; color: #333333; gridline-color: #EDEDED; }
            QHeaderView::section { background-color: #F0F0F0; color: #000000; font-weight: bold; border: none; border-bottom: 3px solid #F1BD4D; padding: 12px; }
        """)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 150)
        main_layout.addWidget(self.table)

        self.dummy_jahre = []

        self.load_table_data(self.dummy_jahre)
        self.search_input.textChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schuljahr hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_jahr_dialog)
        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()

        btn_import = QPushButton("📥 Schuljahre importieren")
        btn_import.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #333333; padding: 8px 20px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 14px; }
            QPushButton:hover, QPushButton:focus { border: 3px solid #000000; }
            QPushButton:pressed { background-color: #F0F0F0; border: 3px solid #000000; color: #333333; }
        """)
        btn_import.clicked.connect(self.import_jahre)
        footer_layout.addWidget(btn_import)
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(get_btn_style("#F1BD4D"))
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)

    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    def show_popup(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(
            "QLabel { color: #000000; font-size: 14px; } QPushButton { color: #000000; padding: 6px 12px; }")
        msg.exec()

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_edit_style = "QPushButton { background: transparent; border: none; font-size: 20px; } QPushButton:hover, QPushButton:pressed { background-color: #E0E0E0; border-radius: 8px; }"
        btn_delete_style = "QPushButton { background: transparent; border: none; font-size: 20px; } QPushButton:hover, QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }"

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
            btn_edit.setFixedSize(45, 45)
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(45, 45)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_delete.setStyleSheet(btn_delete_style)

            btn_edit.clicked.connect(lambda ch, jid=jahr[0]: self.edit_jahr(jid))
            btn_delete.clicked.connect(lambda ch, jid=jahr[0]: self.delete_jahr(jid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 2, action_widget)

    def open_jahr_dialog(self):
        d = SchuljahrDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            max_num = max([int(j[0].split('_')[-1]) for j in self.dummy_jahre if j[0].startswith("SJ_")] + [0])
            self.dummy_jahre.append((f"SJ_{max_num + 1:03d}", name))
            self.filter_table()

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
                            if name and name not in [j[1] for j in self.dummy_jahre]:
                                max_num = max(
                                    [int(j[0].split('_')[-1]) for j in self.dummy_jahre if j[0].startswith("SJ_")] + [
                                        0])
                                self.dummy_jahre.append((f"SJ_{max_num + 1:03d}", name))
                                imported_count += 1
                self.filter_table()
                self.show_popup("Erfolgreich",
                                f"CSV-Datei importiert!\n\nEs wurden {imported_count} Schuljahre hinzugefügt.")
            except Exception as e:
                self.show_popup("Fehler", f"Fehler beim Import:\n{e}")
        else:
            self.show_popup("Fehler", "Bitte eine .csv oder .xlsx auswählen.")