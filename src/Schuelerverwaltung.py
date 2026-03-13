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
                             QFileDialog, QMessageBox)  # Mustafa Demiral: QFileDialog für die Dateiauswahl hinzugefügt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from db_access import fetch_all, fetch_one, execute


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
    def __init__(self, parent=None, class_options=None, student_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neuer Schüler" if not student_data else "Schüler bearbeiten")
        self.setFixedSize(420, 380)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #333333; font-weight: bold; }
            QLineEdit, QComboBox {
                background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 4px; padding: 5px; color: #333333; font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #F1BD4D; }
        """)

        if class_options is None:
            class_options = []

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Eingabefelder
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("Studierende-ID eingeben")

        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname eingeben")
        self.input_nachname = QLineEdit()
        self.input_nachname.setPlaceholderText("Nachname eingeben")
        self.combo_klasse = QComboBox()
        self.combo_klasse.addItem("Bitte wählen...", None)
        for class_id, class_label in class_options:
            self.combo_klasse.addItem(class_label, class_id)
        self.combo_status = QComboBox()
        self.combo_status.addItems(["AKTIV", "INAKTIV"])

        # Fehlermeldung (standardmäßig versteckt)
        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic; font-weight: normal;")
        self.error_label.hide()

        # Ahmet: Bestehende Daten laden, falls Bearbeitungsmodus
        if student_data:
            self.input_id.setText(str(student_data["id"]))
            self.input_id.setReadOnly(True)
            self.input_id.setStyleSheet("background:#F3F3F3;")
            self.input_nachname.setText(student_data["nachname"])
            self.input_vorname.setText(student_data["vorname"])
            self.combo_status.setCurrentText(student_data["status"])
            class_id = student_data["class_id"]
            for i in range(self.combo_klasse.count()):
                if self.combo_klasse.itemData(i) == class_id:
                    self.combo_klasse.setCurrentIndex(i)
                    break

        form_layout.addRow(QLabel("Studierende-ID*:"), self.input_id)
        form_layout.addRow(QLabel("Vorname*:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname*:"), self.input_nachname)
        form_layout.addRow(QLabel("Status*:"), self.combo_status)
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
        sid = self.input_id.text().strip()
        v = self.input_vorname.text().strip()
        n = self.input_nachname.text().strip()
        status = self.combo_status.currentText().strip()
        class_id = self.combo_klasse.currentData()

        self.input_id.setStyleSheet("")
        self.input_vorname.setStyleSheet("")
        self.input_nachname.setStyleSheet("")
        self.combo_status.setStyleSheet("")
        self.combo_klasse.setStyleSheet("")

        errors = []
        if not sid:
            self.input_id.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Studierende-ID ist ein Pflichtfeld.")
        elif not sid.isdigit():
            self.input_id.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Studierende-ID muss eine Zahl sein.")

        if not v:
            self.input_vorname.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Vorname ist ein Pflichtfeld.")
        if not n:
            self.input_nachname.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Nachname ist ein Pflichtfeld.")
        if status not in ("AKTIV", "INAKTIV"):
            self.combo_status.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Status muss AKTIV oder INAKTIV sein.")
        if class_id is None:
            self.combo_klasse.setStyleSheet("border: 2px solid #D32F2F")
            errors.append("Schulklasse ist ein Pflichtfeld.")

        if errors:
            self.error_label.setText(errors[0])
            self.error_label.show()
            return

        self.accept()


# --- Mustafa: Haupt-Widget der Schülerverwaltung ---
class SchuelerverwaltungWidget(QWidget):
    def __init__(self, cfg: dict, parent=None):
        super(SchuelerverwaltungWidget, self).__init__(parent)
        self.cfg = cfg
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
        self.filter_combo.addItem("Klassen", None)
        self.filter_combo.setFixedWidth(200)
        self.filter_combo.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;")
        action_layout.addWidget(self.filter_combo)

        main_layout.addLayout(action_layout)

        # Mustafa: Definition der Haupttabelle
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Nachname", "Vorname", "Status", "Klasse", "Aktionen"])
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
        self.table.setColumnWidth(3, 110)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 150)

        main_layout.addWidget(self.table)

        # Daten laden und Signale verknüpfen
        self.class_options = self.load_classes()
        self.students = self.load_students()
        self._populate_class_filter()
        self.load_table_data(self.students)
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

    def load_classes(self) -> list[tuple[int, str]]:
        sql = """
            SELECT sk.schulklasse_id, sk.name, sj.jahr
            FROM Schulklasse sk
            JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
            ORDER BY sj.jahr, sk.name;
        """
        try:
            rows = fetch_all(self.cfg, sql)
        except Exception as e:
            print(f"DB Fehler (load_classes): {e}")
            QMessageBox.critical(self, "Datenbankfehler", "Schulklassen konnten nicht geladen werden.")
            return []

        return [(int(r[0]), f"{r[1]} ({r[2]})") for r in rows]

    def load_students(self) -> list[dict]:
        sql = """
            SELECT s.studierende_id, s.nachname, s.vorname, s.status,
                   s.schulklasse_id, sk.name, sj.jahr
            FROM Studierende s
            JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
            JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
            ORDER BY s.studierende_id;
        """
        try:
            rows = fetch_all(self.cfg, sql)
        except Exception as e:
            print(f"DB Fehler (load_students): {e}")
            QMessageBox.critical(self, "Datenbankfehler", "Studierende konnten nicht geladen werden.")
            return []

        data = []
        for r in rows:
            data.append({
                "id": str(r[0]),
                "nachname": r[1],
                "vorname": r[2],
                "status": r[3],
                "class_id": int(r[4]),
                "class_label": f"{r[5]} ({r[6]})",
            })
        return data

    def _populate_class_filter(self):
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("Klassen", None)
        for class_id, class_label in self.class_options:
            self.filter_combo.addItem(class_label, class_id)
        self.filter_combo.blockSignals(False)

    # Funktion: Befüllt die Tabelle mit den Schülerdaten
    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        for row, student in enumerate(data_list):
            columns = [
                student["id"],
                student["nachname"],
                student["vorname"],
                student["status"],
                student["class_label"],
            ]
            for col in range(5):
                item = QTableWidgetItem(columns[col])
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
            btn_edit.clicked.connect(lambda ch, sid=student["id"]: self.edit_student(sid))

            # Löschen Button
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(45, 45)
            btn_delete.setStyleSheet(
                "QPushButton { background: transparent; border: none; font-size: 20px; } "
                "QPushButton:hover { background-color: #FFCDD2; border-radius: 8px; }"
                "QPushButton:pressed { background-color: #FFCDD2; border-radius: 8px; }")

            btn_delete.clicked.connect(lambda ch, sid=student["id"]: self.delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    # Mustafa: Öffnet den Dialog zum Hinzufügen eines neuen Schülers
    def open_student_dialog(self):
        d = StudentDialog(self, class_options=self.class_options)
        if d.exec() == QDialog.DialogCode.Accepted:
            sid = d.input_id.text().strip()
            vorname = d.input_vorname.text().strip()
            nachname = d.input_nachname.text().strip()
            status = d.combo_status.currentText().strip()
            class_id = d.combo_klasse.currentData()

            try:
                exists = fetch_one(self.cfg, "SELECT 1 FROM Studierende WHERE studierende_id = %s;", (sid,))
                if exists:
                    QMessageBox.warning(self, "Hinweis", "Studierende-ID existiert bereits.")
                    return

                execute(
                    self.cfg,
                    "INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id) VALUES (%s, %s, %s, %s, %s);",
                    (sid, vorname, nachname, status, class_id),
                )
                QMessageBox.information(self, "Erfolg", "Studierende*r wurde angelegt.")
                self.students = self.load_students()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (insert student): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Studierende*r konnte nicht angelegt werden.")

    # Funktion: Bearbeitet einen bestehenden Schüler-Datensatz
    def edit_student(self, sid):
        target = None
        for s in self.students:
            if s["id"] == str(sid):
                target = s
                break
        if not target:
            QMessageBox.warning(self, "Hinweis", "Studierende*r wurde nicht gefunden.")
            return

        d = StudentDialog(self, class_options=self.class_options, student_data=target)
        if d.exec() == QDialog.DialogCode.Accepted:
            vorname = d.input_vorname.text().strip()
            nachname = d.input_nachname.text().strip()
            status = d.combo_status.currentText().strip()
            class_id = d.combo_klasse.currentData()
            try:
                execute(
                    self.cfg,
                    "UPDATE Studierende SET vorname = %s, nachname = %s, status = %s, schulklasse_id = %s WHERE studierende_id = %s;",
                    (vorname, nachname, status, class_id, sid),
                )
                QMessageBox.information(self, "Erfolg", "Studierende*r wurde aktualisiert.")
                self.students = self.load_students()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (update student): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Studierende*r konnte nicht aktualisiert werden.")

    # Funktion: Löscht einen Schüler nach Bestätigung
    def delete_student(self, sid):
        confirm = DeleteConfirmDialog(self)
        if confirm.exec() == QDialog.DialogCode.Accepted:
            try:
                in_use = fetch_one(
                    self.cfg,
                    "SELECT 1 FROM Ausleihe_Aktuell WHERE studierende_id = %s LIMIT 1;",
                    (sid,),
                )
                if in_use:
                    QMessageBox.warning(
                        self,
                        "Löschen nicht möglich",
                        "Datensatz kann nicht gelöscht werden, da noch aktive Verknüpfungen bestehen.",
                    )
                    return

                execute(self.cfg, "DELETE FROM Studierende WHERE studierende_id = %s;", (sid,))
                QMessageBox.information(self, "Erfolg", "Studierende*r wurde gelöscht.")
                self.students = self.load_students()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (delete student): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Studierende*r konnte nicht gelöscht werden.")

    # Ahmet: Such- und Filterlogik für die Tabellenanzeige
    def filter_table(self):
        txt = self.search_input.text().lower()
        class_id = self.filter_combo.currentData()
        filtered = []
        for s in self.students:
            hay = f"{s['id']} {s['nachname']} {s['vorname']} {s['status']} {s['class_label']}".lower()
            if txt in hay and (class_id is None or s["class_id"] == class_id):
                filtered.append(s)
        self.load_table_data(filtered)

    # Mustafa Demiral: Dialog zur Dateiauswahl für den CSV Import
    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV Datei auswählen", "", "CSV Dateien (*.csv)")
        if file_path:
            try:
                class_map = {label: class_id for class_id, label in self.class_options}
                inserted = 0
                skipped = 0
                with open(file_path, mode='r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file, delimiter=';')

                    header_skipped = False
                    for row in csv_reader:
                        # Überspringe die allererste Zeile (Header)
                        if not header_skipped:
                            header_skipped = True
                            continue

                        if len(row) >= 4:
                            student_id = row[0].strip()
                            vorname = row[1].strip()
                            nachname = row[2].strip()
                            klasse = row[3].strip()
                            class_id = class_map.get(klasse)

                            if not student_id or not student_id.isdigit() or not vorname or not nachname or class_id is None:
                                skipped += 1
                                continue

                            exists = fetch_one(
                                self.cfg,
                                "SELECT 1 FROM Studierende WHERE studierende_id = %s;",
                                (student_id,),
                            )
                            if exists:
                                skipped += 1
                                continue

                            execute(
                                self.cfg,
                                "INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id) VALUES (%s, %s, %s, %s, %s);",
                                (student_id, vorname, nachname, "AKTIV", class_id),
                            )
                            inserted += 1

                self.students = self.load_students()
                self.filter_table()
                QMessageBox.information(
                    self,
                    "CSV Import",
                    f"Import abgeschlossen. Eingefügt: {inserted}, Übersprungen: {skipped}.",
                )
            except Exception as e:
                print(f"Fehler beim Importieren der CSV: {e}")
                QMessageBox.critical(self, "CSV Import", "CSV konnte nicht importiert werden.")
