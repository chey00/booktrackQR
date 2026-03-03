# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: SchuelerverwaltungWidget (GUI Design & Logik)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Stand: Finales Layout mit Dokumentation (Weißer Import-Button, Tabellen-Design)
# ------------------------------------------------------------------------------
import os
import csv  # Luis Overrath: Import für die CSV-Verarbeitung
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
                             QFileDialog, QMessageBox)  # Mustafa Demiral: QMessageBox hinzugefügt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


# Hilfsfunktion für einheitliche Buttons (spart sehr viel Code)
def get_btn_style(bg_color, text_color="white"):
    return f"""
        QPushButton {{ background-color: {bg_color}; color: {text_color}; padding: 8px 20px; 
        border: 3px solid {bg_color}; border-radius: 6px; font-weight: bold; font-size: 14px; }}
        QPushButton:hover, QPushButton:focus {{ border: 3px solid #000000; }}
        QPushButton:pressed {{ background-color: #444444; border: 3px solid #000000; color: white; }}
    """


# --- Ahmet: Bestätigungsdialog für das Löschen von Datensätzen ---
class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(400, 180)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel("⚠️ Möchten Sie diesen Schüler wirklich\nunwiderruflich löschen?")
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

        # Zuweisung der Breite (Alle exakt gleich breit: 250px) per Schleife kompakter
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

        # Filter-Leiste: Suche und Klassenfilter (Breiten unterschiedlich)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed);
        self.table.setColumnWidth(0, 140)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed);
        self.table.setColumnWidth(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed);
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed);
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
        # EXPLIZIT WEISSER HINTERGRUND MIT GRAUEM RAND UND SCHWARZEM FOKUS
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

            btn_edit = QPushButton("✏️");
            btn_edit.setFixedSize(45, 45)
            btn_delete = QPushButton("🗑️");
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
        if DeleteConfirmDialog(self).exec() == QDialog.DialogCode.Accepted:
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

    # Hilfsfunktion für Benachrichtigungen (Reduziert doppelten Code)
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