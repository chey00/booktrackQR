# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: BuchverwaltungWidget (GUI Design & Logik)
# Autoren:
# - Harun: Dialoge (DeleteConfirmDialog, BookDialog) + Validierung
# - Batuhan: BuchverwaltungWidget (Layout, Tabelle, Sortierung, Bestand +/- , Aktionen)
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from db_access import fetch_all, fetch_one, execute


# ==============================================================================
# Harun: DeleteConfirmDialog
# Zweck: Bestätigungsdialog, damit man Bücher nicht aus Versehen löscht.
# ==============================================================================
class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Fenster-Einstellungen
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(350, 180)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Grundlayout im Dialog
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Hinweistext / Warnung
        self.label = QLabel("⚠️ Möchten Sie dieses Buch wirklich\nunwiderruflich löschen?")
        self.label.setFont(QFont("Open Sans", 11, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(self.label)

        # Buttons: Abbrechen / Löschen
        btn_layout = QHBoxLayout()
        self.btn_no = QPushButton("Abbrechen")
        self.btn_yes = QPushButton("Löschen")

        # Styling der Buttons (Rot = gefährlich / Grau = neutral)
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

        # Dialog-Ergebnis: accept() = OK / reject() = Abbrechen
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)


# ==============================================================================
# Harun: BookDialog
# Zweck: Dialog zum "Buch hinzufügen" und "Buch bearbeiten"
# - Bei Bearbeiten ist ISBN read-only (damit Schlüssel nicht geändert wird).
# - validate_and_save() prüft Pflichtfelder + Bestand muss Zahl sein.
# ==============================================================================
class BookDialog(QDialog):
    def __init__(self, parent=None, book_data=None):
        super().__init__(parent)

        self.setWindowTitle("Neues Buch" if not book_data else "Buch bearbeiten")
        self.setFixedSize(420, 320)

        # Grund-Stylesheet für Dialog + Eingabefelder
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #333333; font-weight: bold; }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #5CB1D6; }
        """)

        layout = QVBoxLayout(self)

        # FormLayout -> Label links, Eingabefeld rechts
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Eingabefelder
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("Titel-ID eingeben")

        self.input_isbn = QLineEdit()
        self.input_isbn.setPlaceholderText("ISBN eingeben")

        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("Titel eingeben")

        self.input_publisher = QLineEdit()
        self.input_publisher.setPlaceholderText("Verlag eingeben")

        self.input_edition = QLineEdit()
        self.input_edition.setPlaceholderText("Auflage eingeben")

        # Fehlermeldung (standardmäßig versteckt)
        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic; font-weight: normal;")
        self.error_label.hide()

        # Bearbeitungsmodus: bestehende Daten in Felder laden
        if book_data:
            # book_data: (titel_id, isbn, titel, verlag, auflage)
            self.input_id.setText(str(book_data[0]))
            self.input_id.setReadOnly(True)  # Titel-ID bleibt fix
            self.input_id.setStyleSheet("background:#F3F3F3;")
            self.input_isbn.setText(book_data[1])
            self.input_title.setText(book_data[2])
            self.input_publisher.setText(book_data[3])
            self.input_edition.setText(str(book_data[4]))

        # Pflichtfelder mit * markiert
        form_layout.addRow(QLabel("Titel-ID*:"), self.input_id)
        form_layout.addRow(QLabel("ISBN*:"), self.input_isbn)
        form_layout.addRow(QLabel("Titel*:"), self.input_title)
        form_layout.addRow(QLabel("Verlag*:"), self.input_publisher)
        form_layout.addRow(QLabel("Auflage*:"), self.input_edition)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()

        # Aktionsbuttons: Abbrechen / Speichern
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")

        # Button-Styles (Grau / Blau)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; padding: 7px 17px; border: 3px solid #E0E0E0; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; color: white; }
        """)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #5CB1D6; color: white; padding: 7px 17px; border: 3px solid #5CB1D6; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)

        # Dialog-Steuerung
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def validate_and_save(self):
        """
        Validierung:
        - Titel-ID, ISBN, Titel, Verlag, Auflage dürfen nicht leer sein
        - Auflage > 0
        - Bei Fehler: rote Rahmen + Fehlermeldung anzeigen
        """
        tid = self.input_id.text().strip()
        isbn = self.input_isbn.text().strip()
        t = self.input_title.text().strip()
        p = self.input_publisher.text().strip()
        e = self.input_edition.text().strip()

        # Reset Rahmen (falls vorher Fehler)
        self.input_id.setStyleSheet("")
        self.input_isbn.setStyleSheet("")
        self.input_title.setStyleSheet("")
        self.input_publisher.setStyleSheet("")
        self.input_edition.setStyleSheet("")

        errors = []
        if not tid:
            self.input_id.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Titel-ID ist ein Pflichtfeld.")
        elif not tid.isdigit():
            self.input_id.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Titel-ID muss eine Zahl sein.")
        if not isbn:
            self.input_isbn.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("ISBN ist ein Pflichtfeld.")
        if not t:
            self.input_title.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Titel ist ein Pflichtfeld.")
        if not p:
            self.input_publisher.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Verlag ist ein Pflichtfeld.")
        if not e:
            self.input_edition.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Auflage ist ein Pflichtfeld.")
        elif not e.isdigit() or int(e) <= 0:
            self.input_edition.setStyleSheet("border: 2px solid #D32F2F;")
            errors.append("Auflage muss größer als 0 sein.")

        if errors:
            self.error_label.setText(errors[0])
            self.error_label.show()
            return

        self.accept()


# ==============================================================================
# Batuhan: BuchverwaltungWidget
# Zweck: Hauptseite der Buchverwaltung
# - Header (Titel + Logo), Breadcrumbs, Titel
# - Actionbar: Suche + "Sortieren nach" Dropdown + Button "Buch hinzufügen"
# - Tabelle mit Bestand (+/-) und Aktionen (Bearbeiten/Löschen)
# - Suchlogik + Sortierlogik (Titel/Verlag/Auflage)
# ==============================================================================
class BuchverwaltungWidget(QWidget):
    def __init__(self, cfg: dict, parent=None):
        super(BuchverwaltungWidget, self).__init__(parent)
        self.cfg = cfg
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # ---------------------------
        # Layout-Grundstruktur
        # ---------------------------
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 30, 50, 50)
        main_layout.setSpacing(15)

        # ================= HEADER =================
        header_layout = QHBoxLayout()

        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)  # sorgt dafür, dass Titel mittig bleibt
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # Logo oben rechts
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

        # ================= BREADCRUMBS =================
        self.back_label = QLabel("Startseite > Hauptmenü > Buchverwaltung")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px;")
        main_layout.addWidget(self.back_label)

        # ================= TITEL =================
        page_title = QLabel("Bücherverwaltung")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #5CB1D6; margin-left: 10px;")
        main_layout.addWidget(page_title)

        # ================= ACTION BAR =================
        # Suche + Sortieren-nach Dropdown + Button "Buch hinzufügen"
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)
        action_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        )
        action_layout.addWidget(self.search_input)

        # >>> ÄNDERUNG: statt Verlag-Filter jetzt Sortierungsauswahl <<<
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sortieren nach: Titel-ID", "ISBN", "Titel", "Verlag", "Auflage"])
        self.sort_combo.setFixedWidth(200)
        self.sort_combo.setStyleSheet(
            "padding: 10px; border: 1px solid #CCCCCC; border-radius: 6px; background-color: #FFFFFF; color: #333333; font-size: 14px;"
        )
        action_layout.addWidget(self.sort_combo)

        action_layout.addStretch()

        btn_add = QPushButton("➕ Buch hinzufügen")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #5CB1D6; color: white; padding: 10px 25px; border: 3px solid #5CB1D6; border-radius: 6px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)
        btn_add.clicked.connect(self.open_book_dialog)
        action_layout.addWidget(btn_add)

        main_layout.addLayout(action_layout)

        # ================= TABLE =================
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Titel-ID", "ISBN", "Titel", "Verlag", "Auflage", "Bestand", "Aktionen"])
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
                border: none; border-bottom: 3px solid #5CB1D6; padding: 12px; 
            }
        """)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   # Titel-ID
        self.table.setColumnWidth(0, 110)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)   # ISBN
        self.table.setColumnWidth(1, 160)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Titel
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Verlag

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)   # Auflage
        self.table.setColumnWidth(4, 120)

        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Bestand
        self.table.setColumnWidth(5, 120)

        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Aktionen
        self.table.setColumnWidth(6, 150)

        main_layout.addWidget(self.table)

        # Tabelle initial befüllen
        self.books = self.load_books()
        self.load_table_data(self.books)

        # Signale: bei Änderungen sofort aktualisieren (Suche + Sortierung)
        self.search_input.textChanged.connect(self.filter_table)
        self.sort_combo.currentTextChanged.connect(self.filter_table)

        # ================= FOOTER =================
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet("""
            QPushButton { background-color: #5CB1D6; color: white; padding: 12px 25px; border: 3px solid #5CB1D6; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { border: 3px solid #333333; }
            QPushButton:pressed { background-color: #444444; border: 3px solid #444444; }
        """)
        footer_layout.addWidget(self.btn_back)
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

    # --------------------------------------------------------------------------
    # Helper: Image-Pfad
    # --------------------------------------------------------------------------
    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), "..", "pic", filename)

    def load_books(self) -> list[dict]:
        sql = """
            SELECT t.titel_id, t.isbn, t.titel, t.verlag, t.auflage,
                   COUNT(e.exemplar_id) AS bestand
            FROM BuchTitel t
            LEFT JOIN BuchExemplar e ON e.isbn = t.isbn
            GROUP BY t.titel_id, t.isbn, t.titel, t.verlag, t.auflage
            ORDER BY t.titel_id;
        """
        try:
            rows = fetch_all(self.cfg, sql)
        except Exception as e:
            print(f"DB Fehler (load_books): {e}")
            QMessageBox.critical(self, "Datenbankfehler", "Buchtitel konnten nicht geladen werden.")
            return []

        data = []
        for r in rows:
            data.append({
                "id": str(r[0]),
                "isbn": r[1],
                "titel": r[2],
                "verlag": r[3],
                "auflage": r[4],
                "bestand": int(r[5]),
            })
        return data

    # --------------------------------------------------------------------------
    # Tabelle befüllen (0..3 normale Items, 4/5 Widgets)
    # --------------------------------------------------------------------------
    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        for row, book in enumerate(data_list):
            columns = [
                book["id"],
                book["isbn"],
                book["titel"],
                book["verlag"],
                book["auflage"],
                book["bestand"],
            ]
            for col in range(6):
                item = QTableWidgetItem(str(columns[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if col in [0, 1, 4, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            self._set_actions_widget(row, book["id"])

    # --------------------------------------------------------------------------
    # Aktionen-Widget (Bearbeiten/Löschen)
    # --------------------------------------------------------------------------
    def _set_actions_widget(self, row, titel_id):
        bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

        action_widget = QWidget()
        action_widget.setStyleSheet(f"background-color: {bg_color};")

        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 0, 5, 0)
        action_layout.setSpacing(15)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(45, 45)
        btn_edit.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { background-color: #E0E0E0; border-radius: 8px; }"
        )
        btn_edit.clicked.connect(lambda ch, x=titel_id: self.edit_book(x))

        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(45, 45)
        btn_delete.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { background-color: #FFCDD2; border-radius: 8px; }"
        )
        btn_delete.clicked.connect(lambda ch, x=titel_id: self.delete_book(x))

        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_delete)

        self.table.setCellWidget(row, 6, action_widget)

    # --------------------------------------------------------------------------
    # Buch hinzufügen
    # --------------------------------------------------------------------------
    def open_book_dialog(self):
        d = BookDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            titel_id = d.input_id.text().strip()
            isbn = d.input_isbn.text().strip()
            titel = d.input_title.text().strip()
            verlag = d.input_publisher.text().strip()
            auflage = int(d.input_edition.text().strip())

            try:
                exists = fetch_one(self.cfg, "SELECT 1 FROM BuchTitel WHERE titel_id = %s;", (titel_id,))
                if exists:
                    QMessageBox.warning(self, "Hinweis", "Titel-ID existiert bereits.")
                    return

                execute(
                    self.cfg,
                    "INSERT INTO BuchTitel (titel_id, titel, verlag, auflage, isbn) VALUES (%s, %s, %s, %s, %s);",
                    (titel_id, titel, verlag, auflage, isbn),
                )
                QMessageBox.information(self, "Erfolg", "Buchtitel wurde angelegt.")
                self.books = self.load_books()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (insert book): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Buchtitel konnte nicht angelegt werden.")

    # --------------------------------------------------------------------------
    # Buch bearbeiten
    # --------------------------------------------------------------------------
    def edit_book(self, titel_id):
        target = None
        for b in self.books:
            if b["id"] == str(titel_id):
                target = b
                break
        if not target:
            QMessageBox.warning(self, "Hinweis", "Buchtitel wurde nicht gefunden.")
            return

        d = BookDialog(self, book_data=(target["id"], target["isbn"], target["titel"], target["verlag"], target["auflage"]))
        if d.exec() == QDialog.DialogCode.Accepted:
            titel = d.input_title.text().strip()
            verlag = d.input_publisher.text().strip()
            auflage = int(d.input_edition.text().strip())
            isbn_val = d.input_isbn.text().strip()
            try:
                execute(
                    self.cfg,
                    "UPDATE BuchTitel SET titel = %s, verlag = %s, auflage = %s, isbn = %s WHERE titel_id = %s;",
                    (titel, verlag, auflage, isbn_val, titel_id),
                )
                QMessageBox.information(self, "Erfolg", "Buchtitel wurde aktualisiert.")
                self.books = self.load_books()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (update book): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Buchtitel konnte nicht aktualisiert werden.")

    # --------------------------------------------------------------------------
    # Buch löschen
    # --------------------------------------------------------------------------
    def delete_book(self, titel_id):
        confirm = DeleteConfirmDialog(self)
        if confirm.exec() == QDialog.DialogCode.Accepted:
            try:
                isbn_row = fetch_one(
                    self.cfg,
                    "SELECT isbn FROM BuchTitel WHERE titel_id = %s;",
                    (titel_id,),
                )
                isbn_val = isbn_row[0] if isbn_row else None
                in_use = None
                if isbn_val:
                    in_use = fetch_one(
                        self.cfg,
                        "SELECT 1 FROM BuchExemplar WHERE isbn = %s LIMIT 1;",
                        (isbn_val,),
                    )
                if in_use:
                    QMessageBox.warning(
                        self,
                        "Löschen nicht möglich",
                        "Datensatz kann nicht gelöscht werden, da noch aktive Verknüpfungen bestehen.",
                    )
                    return

                execute(self.cfg, "DELETE FROM BuchTitel WHERE titel_id = %s;", (titel_id,))
                QMessageBox.information(self, "Erfolg", "Buchtitel wurde gelöscht.")
                self.books = self.load_books()
                self.filter_table()
            except Exception as e:
                print(f"DB Fehler (delete book): {e}")
                QMessageBox.critical(self, "Datenbankfehler", "Buchtitel konnte nicht gelöscht werden.")

    # --------------------------------------------------------------------------
    # Suche + Sortierung
    # - Suche: filtert nach ISBN/Titel/Verlag/Auflage
    # - Sortierung: nach ISBN (Standard) oder Titel/Verlag/Auflage
    # --------------------------------------------------------------------------
    def filter_table(self):
        txt = self.search_input.text().lower().strip()
        sort_opt = self.sort_combo.currentText()

        # 1) Filtern (Suche)
        filtered = []
        for b in self.books:
            hay = f"{b['id']} {b['isbn']} {b['titel']} {b['verlag']} {b['auflage']} {b['bestand']}".lower()
            if txt in hay:
                filtered.append(b)

        # 2) Sortieren (dein gewünschter "Filter")
        if sort_opt == "ISBN":
            filtered.sort(key=lambda x: x["isbn"].lower())
        elif sort_opt == "Titel":
            filtered.sort(key=lambda x: x["titel"].lower())
        elif sort_opt == "Verlag":
            filtered.sort(key=lambda x: x["verlag"].lower())
        elif sort_opt == "Auflage":
            filtered.sort(key=lambda x: x["auflage"])
        else:
            filtered.sort(key=lambda x: int(x["id"]))  # Standard: Titel-ID

        self.load_table_data(filtered)
