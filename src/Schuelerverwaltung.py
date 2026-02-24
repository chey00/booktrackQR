# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: SchuelerverwaltungWidget (GUI Design & Validierungs-Logik)
# Stand: GUI mit TableWidget und Validierungs-Dialog
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
                             QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon


class StudentDialog(QDialog):
    """
    Dialog-Fenster zum Anlegen oder Bearbeiten eines Schülers.
    Enthält die Validierungslogik für Pflichtfelder (Klasse).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neuer Schüler")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)

        # Formular Layout
        form_layout = QFormLayout()

        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname")
        self.input_nachname = QLineEdit()
        self.input_nachname.setPlaceholderText("Nachname")

        # Klassen-Dropdown
        self.combo_klasse = QComboBox()
        self.combo_klasse.addItems(["Bitte wählen...", "10A", "10B", "11A", "11B"])

        # Fehler-Label (Standardmäßig versteckt)
        self.error_label = QLabel("Bitte eine Klasse auswählen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        # Felder zum Formular hinzufügen
        form_layout.addRow(QLabel("Vorname:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname:"), self.input_nachname)
        form_layout.addRow(QLabel("Klasse*:"), self.combo_klasse)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)  # Unter das Dropdown setzen
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)  # Eigene Validierungs-Methode

        # Styling der Buttons im Modal
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #F1BD4D; border: none; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #D9A840; }
        """)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; border: none; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #CCCCCC; }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def validate_and_save(self):
        """Prüft, ob die Klasse ausgewählt wurde (Typischer Fehlerfall der User Story)"""
        if self.combo_klasse.currentText() == "Bitte wählen...":
            # Fehlerfall: Roter Rahmen und Fehlermeldung anzeigen
            self.combo_klasse.setStyleSheet("border: 2px solid #D32F2F; border-radius: 3px; padding: 2px;")
            self.error_label.show()
        else:
            # Alles OK: Fehler verstecken und Dialog erfolgreich schließen
            self.combo_klasse.setStyleSheet("")
            self.error_label.hide()
            self.accept()  # Schließt den Dialog mit "Accepted" Status


class SchuelerverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super(SchuelerverwaltungWidget, self).__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")  # Grundhintergrund

        main_layout = QVBoxLayout()

        # --- HEADER BEREICH (Kopie vom CentralWidget für Konsistenz) ---
        header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        dummy_left.setStyleSheet("background: transparent;")
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = self.get_image_path("technikerschule_logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("Logo nicht gefunden")
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Breadcrumb Navigation
        self.back_label = QLabel("Startseite > Hauptmenü > Schülerverwaltung")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px;")
        main_layout.addWidget(self.back_label)

        # Seiten-Titel
        page_title = QLabel("Schülerverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #F1BD4D; margin-left: 10px;")  # Gelb/Orange vom Hauptmenü
        main_layout.addWidget(page_title)

        # --- ACTION BAR (Suche, Filter, Buttons) ---
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 10)

        # Suche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Name...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
        action_layout.addWidget(self.search_input)

        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Filter: Alle Klassen", "10A", "10B", "11A", "11B"])
        self.filter_combo.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
        action_layout.addWidget(self.filter_combo)

        action_layout.addStretch()  # Schiebt die Buttons nach rechts

        # Import Button
        btn_import = QPushButton("📤 CSV Importieren")
        btn_import.setStyleSheet("padding: 8px 15px; border: 1px solid #CCC; border-radius: 4px; background: white;")
        action_layout.addWidget(btn_import)

        # Hinzufügen Button (Primär)
        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #F1BD4D; color: white; padding: 8px 15px; border: none; border-radius: 4px; font-weight: bold;}
            QPushButton:hover { background-color: #D9A840; }
        """)
        btn_add.clicked.connect(self.open_student_dialog)  # Verbindet Button mit dem Dialog
        action_layout.addWidget(btn_add)

        main_layout.addLayout(action_layout)

        # --- TABELLE ---
        self.table = QTableWidget(0, 5)  # 0 Zeilen (werden gefüllt), 5 Spalten
        self.table.setHorizontalHeaderLabels(["ID", "Nachname", "Vorname", "Klasse", "Aktionen"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E0E0E0; }
            QHeaderView::section { background-color: #F5F5F5; font-weight: bold; border: 1px solid #E0E0E0; padding: 4px; }
            QTableWidget::item { padding: 5px; }
        """)
        main_layout.addWidget(self.table)

        # Testdaten laden
        self.load_dummy_data()

        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)

    def get_image_path(self, filename):
        base_dir = os.path.dirname(__file__)
        return os.path.join(base_dir, "..", "pic", filename)

    def open_student_dialog(self):
        """Öffnet das Modal zum Erstellen/Bearbeiten und fängt das Ergebnis ab."""
        dialog = StudentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Hier würde später die Datenbank-Logik greifen
            print(
                f"Schüler {dialog.input_vorname.text()} {dialog.input_nachname.text()} für Klasse {dialog.combo_klasse.currentText()} gespeichert!")

    def load_dummy_data(self):
        """Füllt die Tabelle mit Testdaten zur Visualisierung."""
        dummy_students = [
            ("101", "Müller", "Max", "10A"),
            ("102", "Schmidt", "Lisa", "10A"),
            ("103", "Weber", "Tom", "10B"),
        ]

        self.table.setRowCount(len(dummy_students))
        for row_idx, student in enumerate(dummy_students):
            for col_idx, data in enumerate(student):
                item = QTableWidgetItem(data)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Zelle schreibgeschützt machen
                self.table.setItem(row_idx, col_idx, item)

            # Aktion-Buttons simulieren (Als reiner Text für das Mockup, später eigene Widgets)
            action_item = QTableWidgetItem("✏️ Bearbeiten | 🗑️ Löschen")
            action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, action_item)