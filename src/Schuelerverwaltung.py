# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: SchuelerverwaltungWidget (GUI Design & Logik)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Stand: Finales Layout mit Dokumentation (Bereinigt um Testdaten)
# ------------------------------------------------------------------------------
import os
import csv  # Luis Overrath: Import für die CSV-Verarbeitung
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
                             QFileDialog)  # Mustafa Demiral: QFileDialog für die Dateiauswahl hinzugefügt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


# --- Ahmet: Bestätigungsdialog für das Löschen von Datensätzen ---
class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(350, 180)
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

        # Styling der Dialog-Buttons
        style_yes = """
            QPushButton { background-color: #D32F2F; color: white; padding: 8px; border: 3px solid #D32F2F; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """
        style_no = """
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 8px; border: 3px solid #E0E0E0; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; color: white; }
        """
        self.btn_yes.setStyleSheet(style_yes)
        self.btn_no.setStyleSheet(style_no)

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
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #333333; font-weight: bold; }
            QLineEdit, QComboBox {
                background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 5px; color: #333333; font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #F1BD4D; }
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
        self.combo_klasse.addItems(["Bitte wählen...", "10A", "10B", "11A", "11B", "FSWI2"])

        # Fehlermeldung (standardmäßig versteckt)
        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic; font-weight: normal;")
        self.error_label.hide()

        # Ahmet: Bestehende Daten laden, falls Bearbeitungsmodus
        if student_data:
            self.input_nachname.setText(student_data[1])
            self.input_vorname.setText(student_data[2])
            self.combo_klasse.setCurrentText(student_data[3])

        form_layout.addRow(QLabel("Vorname*:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname*:"), self.input_nachname)
        form_layout.addRow(QLabel("Klasse*:"), self.combo_klasse)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()

        # Speicher- und Abbrechen-Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")

        # Styling der Dialog-Aktionsbuttons
        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 7px 17px; border: 3px solid #E0E0E0; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; color: white; }
        """)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #F1BD4D; color: white; padding: 7px 17px; border: 3px solid #F1BD4D; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    # Validierung: Prüft ob alle Felder korrekt ausgefüllt sind
    def validate_and_save(self):
        v, n, k = self.input_vorname.text().strip(), self.input_nachname.text().strip(), self.combo_klasse.currentText()
        self.input_vorname.setStyleSheet("")
        self.input_nachname.setStyleSheet("")
        self.combo_klasse.setStyleSheet("")

        if not v or not n or k == "Bitte wählen...":
            if not v: self.input_vorname.setStyleSheet("border: 2px solid #D32F2F")
            if not n: self.input_nachname.setStyleSheet("border: 2px solid #D32F2F")
            if k == "Bitte wählen...": self.combo_klasse.setStyleSheet("border: 2px solid #D32F2F")
            self.error_label.show()
        else:
            self.accept()


# --- Mustafa: Haupt-Widget der Schülerverwaltung ---
class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super(SchuelerverwaltungWidget, self).__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        main_layout = QVBoxLayout()
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
        logo_path = self.get_image_path("technikerschule_logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)

        # Navigation-Anzeige (Breadcrumbs)
        self.back_label = QLabel("Startseite > Hauptmenü > Schülerverwaltung")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        # Seitentitel
        page_title = QLabel("Schülerverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #F1BD4D; margin-left: 10px;")
        main_layout.addWidget(page_title)

        # Filter-Leiste: Suche und Klassenfilter (Rechtsbündig durch Stretch)
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)
        action_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;")
        action_layout.addWidget(self.search_input)

        action_layout.addStretch() # Mustafa Demiral: Schiebt den Filter nach rechts

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Klassen", "FSKI 2026", "FSWI 2025", "FSWI 2026", "FSMT 2025", "FSMT 2026", "FSMB 2025", "FSMB 2026"])
        self.filter_combo.setFixedWidth(200)
        self.filter_combo.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;")
        action_layout.addWidget(self.filter_combo)

        main_layout.addLayout(action_layout)

        # Mustafa: Definition der Haupttabelle
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nachname", "Vorname", "Klasse", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; alternate-background-color: #F9F9F9; border: 1px solid #E0E0E0; 
                border-radius: 8px; gridline-color: #EDEDED; font-size: 15px; color: #333333; 
            }
            QHeaderView::section { 
                background-color: #F0F0F0; color: #000000; font-weight: bold; 
                border: none; border-bottom: 3px solid #F1BD4D; padding: 12px; 
            }
        """)
        self.table.verticalHeader().setVisible(False)

        # Tabellenspalten-Konfiguration
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 100)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 150)

        main_layout.addWidget(self.table)

        # --- Initialisierung der Datenliste (Leer zu Beginn) ---
        self.dummy_students = []

        # Daten laden und Signale verknüpfen
        self.load_table_data(self.dummy_students)
        self.search_input.textChanged.connect(self.filter_table)
        self.filter_combo.currentTextChanged.connect(self.filter_table)

        # --- FOOTER BEREICH ---
        footer_layout = QHBoxLayout()

        # Schüler hinzufügen Button (Links)
        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #F1BD4D; color: white; padding: 10px 25px; 
            border: 3px solid #F1BD4D; border-radius: 6px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)
        btn_add.clicked.connect(self.open_student_dialog)
        footer_layout.addWidget(btn_add)

        footer_layout.addStretch() # Mustafa Demiral: Zentrierungshilfe

        # Mustafa Demiral: CSV-Import Button (Mitte, weißer Hintergrund)
        btn_import = QPushButton("📥 CSV Import")
        btn_import.setStyleSheet("""
            QPushButton { 
                background-color: #FFFFFF; 
                color: #333333; 
                padding: 10px 25px; 
                border: 3px solid #E0E0E0; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #F0F0F0; }
        """)
        btn_import.clicked.connect(self.import_csv)
        footer_layout.addWidget(btn_import)

        footer_layout.addStretch() # Mustafa Demiral: Zentrierungshilfe

        # Zurück-Button (Rechts)
        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet("""
            QPushButton { background-color: #F1BD4D; color: white; padding: 12px 25px; 
            border: 3px solid #F1BD4D; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)
        footer_layout.addWidget(self.btn_back)

        main_layout.addLayout(footer_layout)
        self.setLayout(main_layout)

    # Hilfsfunktion zum Laden von Bildern
    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    # Funktion: Befüllt die Tabelle mit den Schülerdaten
    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        for row, student in enumerate(data_list):
            for col in range(4):
                item = QTableWidgetItem(student[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if col in [0, 3]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            # Hintergrundfarbe für Aktions-Widget anpassen (wegen AlternatingRowColors)
            bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

            # Container für Edit- und Delete-Buttons in der Tabelle
            action_widget = QWidget()
            action_widget.setStyleSheet(f"background-color: {bg_color}")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setSpacing(15)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Bearbeiten Button
            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(45, 45)
            btn_edit.setStyleSheet(
                "QPushButton { background: transparent; border: none; font-size: 20px; } "
                "QPushButton:hover { background-color: #E0E0E0; border-radius: 8px; }"
                "QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }")
            btn_edit.clicked.connect(lambda ch, sid=student[0]: self.edit_student(sid))

            # Löschen Button
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(45, 45)
            btn_delete.setStyleSheet(
                "QPushButton { background: transparent; border: none; font-size: 20px; } "
                "QPushButton:hover { background-color: #FFCDD2; border-radius: 8px; }"
                "QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }")

            btn_delete.clicked.connect(lambda ch, sid=student[0]: self.delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 4, action_widget)

    # Mustafa: Öffnet den Dialog zum Hinzufügen eines neuen Schülers
    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            # Falls Liste leer, fange mit ID 101 an
            new_id = str(max([int(s[0]) for s in self.dummy_students]) + 1) if self.dummy_students else "101"
            self.dummy_students.append(
                (new_id, d.input_nachname.text(), d.input_vorname.text(), d.combo_klasse.currentText()))
            self.filter_table()

    # Funktion: Bearbeitet einen bestehenden Schüler-Datensatz
    def edit_student(self, sid):
        for i, s in enumerate(self.dummy_students):
            if s[0] == sid:
                d = StudentDialog(self, student_data=s)
                if d.exec() == QDialog.DialogCode.Accepted:
                    self.dummy_students[i] = (sid, d.input_nachname.text(), d.input_vorname.text(),
                                              d.combo_klasse.currentText())
                    self.filter_table()
                break

    # Funktion: Löscht einen Schüler nach Bestätigung
    def delete_student(self, sid):
        confirm = DeleteConfirmDialog(self)
        if confirm.exec() == QDialog.DialogCode.Accepted:
            self.dummy_students = [s for s in self.dummy_students if s[0] != sid]
            self.filter_table()

    # Ahmet: Such- und Filterlogik für die Tabellenanzeige
    def filter_table(self):
        txt, cls = self.search_input.text().lower(), self.filter_combo.currentText()
        filtered = [s for s in self.dummy_students if
                    (txt in s[0].lower() or txt in s[1].lower() or txt in s[2].lower()) and (
                            cls == "Klassen" or cls == s[3])]
        self.load_table_data(filtered)

    # Mustafa Demiral: Dialog zur Dateiauswahl für den CSV Import
    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV Datei auswählen", "", "CSV Dateien (*.csv)")
        if file_path:
            # Luis Overrath: Einlesen der CSV-Datei und Aktualisieren der Datenliste
            try:
                # Nutze utf-8, häufiges Trennzeichen in DE ist Semikolon
                with open(file_path, mode='r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file, delimiter=';')

                    header_skipped = False
                    for row in csv_reader:
                        # Überspringe die allererste Zeile (Header)
                        if not header_skipped:
                            header_skipped = True
                            continue

                        # Luis Overrath: Angepasst an die Spalten der Testdaten (ID, Vorname, Nachname, Klasse)
                        if len(row) >= 4:
                            student_id = row[0].strip()
                            vorname = row[1].strip()
                            nachname = row[2].strip()
                            klasse = row[3].strip()

                            # Nur hinzufügen, wenn ID noch nicht existiert
                            existing_ids = [s[0] for s in self.dummy_students]
                            if student_id not in existing_ids:
                                self.dummy_students.append((student_id, nachname, vorname, klasse))

                # Aktualisiere die UI-Tabelle
                self.filter_table()
            except Exception as e:
                print(f"Fehler beim Importieren der CSV: {e}")