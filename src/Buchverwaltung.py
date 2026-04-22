# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
#
# Modul: BuchverwaltungWidget (GUI Design & Logik)
# Autoren:
# - Harun: Dialoge (DeleteConfirmDialog, BookDialog) + Validierung
# - Mustafa & Ahmet: ISBN Scanner Integration (Kamera) & Multi-API-Autofill
# - Batuhan: BuchverwaltungWidget (Layout, Tabelle, Sortierung, Bestand +/- , Aktionen)
# - René + Georg + Denis: Integration Lade-Indikator & Fehlerbehandlung
#
# Refactoring-Hinweis:
# - Header, Breadcrumb, Seitentitel und Footer werden jetzt zentral
#   über BasePageWidget bereitgestellt.
# - Dadurch wird Code-Duplikation reduziert und das Layout ist
#   konsistent mit den anderen GUI-Ansichten.
# ------------------------------------------------------------------------------

import requests  # Import für die Google Books & OpenLibrary API (Mustafa & Ahmet)
import re  # Import für Datums-Extraktion
from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QComboBox, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from loading_widgets import LoadingTableStack
from database_manager import DatabaseManager
from base_page import BasePageWidget
from ISBN_Scanner import scan_and_return_isbn  # Import Mustafa & Ahmet

# ==============================================================================
# Gemeinsame Styles
# Zweck:
# - Vereinheitlichung der Rundungen und Hover-Effekte
# - Sichtbare Rückmeldung beim Überfahren mit der Maus
# ==============================================================================
BUTTON_RADIUS = 10


def primary_button_style(color: str) -> str:
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            padding: 10px 18px;
            border: 3px solid {color};
            border-radius: {BUTTON_RADIUS}px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            border: 3px solid #333333;
            background-color: {color};
        }}
        QPushButton:pressed {{
            background-color: #444444;
            border: 3px solid #444444;
        }}
        QPushButton:disabled {{
            background-color: #CFCFCF;
            border: 3px solid #CFCFCF;
            color: #888888;
        }}
    """


def neutral_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: #E0E0E0;
            color: #333333;
            padding: 10px 18px;
            border: 3px solid #E0E0E0;
            border-radius: {BUTTON_RADIUS}px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            border: 3px solid #333333;
            background-color: #D7D7D7;
        }}
        QPushButton:pressed {{
            background-color: #444444;
            border: 3px solid #444444;
            color: white;
        }}
    """


def danger_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: #D32F2F;
            color: white;
            padding: 10px 18px;
            border: 3px solid #D32F2F;
            border-radius: {BUTTON_RADIUS}px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            border: 3px solid #333333;
            background-color: #D32F2F;
        }}
        QPushButton:pressed {{
            background-color: #444444;
            border: 3px solid #444444;
        }}
    """


def input_style(accent_color: str) -> str:
    return f"""
        QLineEdit {{
            padding: 10px;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            background-color: #FFFFFF;
            color: #000000;
            font-size: 14px;
        }}
        QLineEdit:hover {{
            border: 1px solid #999999;
        }}
        QLineEdit:focus {{
            border: 2px solid {accent_color};
        }}
        QLineEdit:disabled {{
            background-color: #F3F3F3;
            color: #888888;
        }}
    """


def combo_style(accent_color: str) -> str:
    return f"""
        QComboBox {{
            padding: 10px;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            background-color: #FFFFFF;
            color: #000000;
            font-size: 14px;
        }}
        QComboBox:hover {{
            border: 1px solid #999999;
        }}
        QComboBox:focus {{
            border: 2px solid {accent_color};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
    """


def icon_button_style(hover_bg: str) -> str:
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            font-size: 20px;
            border-radius: {BUTTON_RADIUS}px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
        }}
        QPushButton:pressed {{
            background-color: #D0D0D0;
        }}
    """


def stock_button_style() -> str:
    return f"""
        QPushButton {{
            background: #E0E0E0;
            border: none;
            font-size: 18px;
            font-weight: bold;
            border-radius: {BUTTON_RADIUS}px;
        }}
        QPushButton:hover {{
            border: 2px solid #333333;
            background-color: #D7D7D7;
        }}
        QPushButton:pressed {{
            background: #444444;
            color: white;
        }}
    """


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
        self.label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        layout.addWidget(self.label)

        # Buttons: Abbrechen / Löschen
        btn_layout = QHBoxLayout()
        self.btn_no = QPushButton("Abbrechen")
        self.btn_yes = QPushButton("Löschen")

        # Styling der Buttons (Rot = gefährlich / Grau = neutral)
        self.btn_yes.setStyleSheet(danger_button_style())
        self.btn_no.setStyleSheet(neutral_button_style())

        # Dialog-Ergebnis: accept() = OK / reject() = Abbrechen
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)


# ==============================================================================
# Harun, Mustafa & Ahmet: BookDialog (Integriert mit Barcode-Scanner & Auto-Fill)
# Zweck: Dialog zum "Buch hinzufügen" und "Buch bearbeiten"
# ==============================================================================
class BookDialog(QDialog):
    def __init__(self, parent=None, book_data=None):
        super().__init__(parent)

        self.setWindowTitle("Neues Buch" if not book_data else "Buch bearbeiten")

        # MAC-FIX: Dialog deutlich breiter gemacht, damit alles reinpasst!
        self.setFixedSize(550, 420)

        # Grund-Stylesheet für Dialog + Eingabefelder
        # MAC-FIX: Farbe hart auf Schwarz (#000000) forciert, plus QToolTip Fix!
        self.setStyleSheet(f"""
            QDialog {{ background-color: #FFFFFF; color: #000000; }}
            QLabel {{ color: #000000; font-weight: bold; font-size: 14px; }}
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px;
                color: #000000;
                font-size: 14px;
            }}
            QLineEdit:hover {{ border: 1px solid #999999; }}
            QLineEdit:focus {{ border: 2px solid #5CB1D6; }}
            QLineEdit::placeholder {{ color: #888888; }}
            QToolTip {{ 
                color: #000000; 
                background-color: #F8F9FA; 
                border: 1px solid #CCCCCC; 
            }}
        """)

        layout = QVBoxLayout(self)

        # FormLayout -> Label links, Eingabefeld rechts
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # --- ISBN Feld + Kamera Button (Mustafa & Ahmet) ---
        isbn_layout = QHBoxLayout()
        isbn_layout.setContentsMargins(0, 0, 0, 0)

        self.input_isbn = QLineEdit()
        self.input_isbn.setPlaceholderText("ISBN eingeben")
        self.input_isbn.setFixedWidth(335)  # Zwingt das Feld, breit zu sein!

        self.btn_scan = QPushButton("📷")
        self.btn_scan.setFixedSize(35, 35)
        self.btn_scan.setStyleSheet(f"""
            QPushButton {{ background-color: #E0E0E0; color: #000000; border: 1px solid #CCCCCC; border-radius: {BUTTON_RADIUS}px; font-size: 16px; }}
            QPushButton:hover {{ background-color: #5CB1D6; color: white; border: 1px solid #5CB1D6; }}
        """)
        self.btn_scan.setToolTip("ISBN scannen & Daten automatisch ausfüllen")
        self.btn_scan.clicked.connect(self.trigger_camera_scan)

        isbn_layout.addWidget(self.input_isbn)
        isbn_layout.addWidget(self.btn_scan)
        isbn_layout.addStretch()
        # ----------------------------------------------------

        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("Titel eingeben")
        self.input_title.setFixedWidth(380)  # Zwingt das Feld, breit zu sein!

        self.input_publisher = QLineEdit()
        self.input_publisher.setPlaceholderText("Verlag eingeben")
        self.input_publisher.setFixedWidth(380)

        self.input_edition = QLineEdit()
        self.input_edition.setPlaceholderText("Auflage eingeben")
        self.input_edition.setFixedWidth(380)

        self.input_stock = QLineEdit()
        self.input_stock.setPlaceholderText("Bestand (Zahl)")
        self.input_stock.setFixedWidth(380)

        # Fehlermeldung (standardmäßig versteckt)
        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic; font-weight: normal;")
        self.error_label.hide()

        # Bearbeitungsmodus: bestehende Daten in Felder laden
        if book_data:
            # book_data: (isbn, titel, verlag, auflage, bestand)
            self.input_isbn.setText(book_data[0])
            self.input_isbn.setReadOnly(True)  # ISBN bleibt fix
            self.input_isbn.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #F3F3F3;
                    border: 1px solid #CCCCCC;
                    border-radius: {BUTTON_RADIUS}px;
                    padding: 10px;
                    color: #000000;
                    font-size: 14px;
                }}
            """)

            # Scanner-Button im Bearbeiten-Modus deaktivieren
            self.btn_scan.setEnabled(False)
            self.btn_scan.setStyleSheet(
                f"background-color: #F3F3F3; color: #CCCCCC; border: 1px solid #CCCCCC; border-radius: {BUTTON_RADIUS}px;")

            self.input_title.setText(book_data[1])
            self.input_publisher.setText(book_data[2])
            self.input_edition.setText(book_data[3])
            self.input_stock.setText(str(book_data[4]))

        # Pflichtfelder mit * markiert
        form_layout.addRow(QLabel("ISBN*:"), isbn_layout)
        form_layout.addRow(QLabel("Titel*:"), self.input_title)
        form_layout.addRow(QLabel("Verlag*:"), self.input_publisher)
        form_layout.addRow(QLabel("Auflage*:"), self.input_edition)
        form_layout.addRow(QLabel("Bestand*:"), self.input_stock)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()

        # Aktionsbuttons: Abbrechen / Speichern
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")

        # Button-Styles (Grau / Blau)
        self.btn_cancel.setStyleSheet(neutral_button_style())
        self.btn_save.setStyleSheet(primary_button_style("#5CB1D6"))

        # Dialog-Steuerung
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    # --- SCANNER & API LOGIK (Mustafa & Ahmet) ---
    def trigger_camera_scan(self):
        self.btn_scan.setText("⏳")
        QApplication.processEvents()

        # MAC-FIX: Wir parken das Fenster kurzzeitig weit außerhalb des sichtbaren Bereichs!
        # So entgehen wir allen Grafik-Bugs und das Fenster blockiert die Kamera nicht mehr.
        alte_position = self.pos()
        self.move(-10000, -10000)
        QApplication.processEvents()

        # Kamera starten
        scanned_isbn = scan_and_return_isbn()

        # Fenster sofort wieder zurück an die alte Position holen
        self.move(alte_position)
        self.raise_()
        self.activateWindow()
        self.btn_scan.setText("📷")

        if scanned_isbn:
            self.input_isbn.setText(scanned_isbn)
            # MAC-FIX: Immer color und background-color mitgeben, damit es nicht weiß wird!
            self.input_isbn.setStyleSheet(
                f"background-color: #FFFFFF; color: #000000; border: 2px solid #4CAF50; border-radius: {BUTTON_RADIUS}px; padding: 10px;")

            # 4. API Abfrage mit Verzögerung, damit die GUI nicht einfriert
            QTimer.singleShot(100, lambda: self.fetch_book_data_from_api(scanned_isbn))

    def fetch_book_data_from_api(self, isbn):
        """Holt Buchdaten von Google Books oder OpenLibrary als Fallback."""
        clean_isbn = isbn.replace("-", "").strip()

        # --- 1. VERSUCH: Google Books API ---
        google_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}"
        try:
            response = requests.get(google_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    volume_info = data["items"][0].get("volumeInfo", {})

                    title = volume_info.get("title", "")
                    publisher = volume_info.get("publisher", "")

                    # WICHTIG: NEUE AUFLAGEN-LOGIK (PBI Fix)
                    edition = volume_info.get("edition", "")  # Manche API-Treffer haben ein echtes 'edition' Feld

                    # Falls keine echte 'edition' gefunden wurde, im Titel/Untertitel danach suchen
                    if not edition:
                        full_title = f"{title} {volume_info.get('subtitle', '')}"
                        # Sucht nach Mustern wie "3. Auflage", "4th Edition", etc.
                        match = re.search(r'(\d+)\.\s*Auflage', full_title, re.IGNORECASE)
                        if match:
                            edition = match.group(1)

                    # Wir ignorieren das publishedDate jetzt komplett für die Auflage!

                    if title:  # Wenn Google etwas gefunden hat, tragen wir es ein und brechen ab
                        self._apply_api_data(title, publisher, edition)
                        return
        except Exception as e:
            print(f"Fehler bei Google API: {e}")

        # --- 2. VERSUCH: OpenLibrary API (Wenn Google das Buch nicht kennt) ---
        openlib_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&jscmd=data&format=json"
        try:
            response = requests.get(openlib_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                key = f"ISBN:{clean_isbn}"
                if key in data:
                    book_info = data[key]
                    title = book_info.get("title", "")

                    # Verlage kommen bei OpenLibrary als Liste
                    publishers = book_info.get("publishers", [])
                    publisher = publishers[0].get("name", "") if publishers else ""

                    # WICHTIG: NEUE AUFLAGEN-LOGIK
                    # OpenLibrary hat oft kein sauberes Auflagen-Feld, wir übergeben hier bewusst einen leeren String (""),
                    # damit der Nutzer gezwungen ist, das Feld manuell auszufüllen.
                    edition = ""

                    if title:  # Wenn OpenLibrary etwas gefunden hat
                        self._apply_api_data(title, publisher, edition)
                        return
        except Exception as e:
            print(f"Fehler bei OpenLibrary API: {e}")

        # --- 3. WENN BEIDE DATENBANKEN DAS BUCH NICHT KENNEN ---
        print("Buch in keinen APIs gefunden (Weder Google noch OpenLibrary).")
        self.input_title.setPlaceholderText("Nicht gefunden - Bitte manuell tippen")
        self.input_publisher.setPlaceholderText("Nicht gefunden - Bitte manuell tippen")

    def _apply_api_data(self, title, publisher, edition):
        """Hilfsfunktion, um die Felder grün zu markieren und zu füllen."""
        # MAC-FIX: Immer color und background-color mitgeben!
        success_style = f"background-color: #FFFFFF; color: #000000; border: 2px solid #4CAF50; border-radius: {BUTTON_RADIUS}px; padding: 10px;"

        if title:
            self.input_title.setText(title)
            self.input_title.setStyleSheet(success_style)
        if publisher:
            self.input_publisher.setText(publisher)
            self.input_publisher.setStyleSheet(success_style)
        if edition:
            self.input_edition.setText(edition)
            self.input_edition.setStyleSheet(success_style)
        else:
            # Falls die API keine echte Auflage gefunden hat, bleibt das Feld leer,
            # wird aber nicht grün markiert, um dem Nutzer zu signalisieren: "Hier musst du ran!"
            self.input_edition.clear()
            self.input_edition.setPlaceholderText("Bitte Auflage manuell eintragen")
            self.input_edition.setStyleSheet(f"""
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px;
            """)

    # ---------------------------------------------

    def validate_and_save(self):
        """
        Validierung:
        - ISBN, Titel, Verlag, Auflage dürfen nicht leer sein
        - Bestand muss eine Zahl sein
        - Bei Fehler: rote Rahmen + Fehlermeldung anzeigen
        """
        isbn = self.input_isbn.text().strip()
        t = self.input_title.text().strip()
        p = self.input_publisher.text().strip()
        e = self.input_edition.text().strip()
        s = self.input_stock.text().strip()

        # MAC-FIX: Immer color und background-color mitgeben!
        default_style = f"""
            background-color: #FFFFFF;
            color: #000000;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            padding: 10px;
        """
        self.input_isbn.setStyleSheet(default_style)
        self.input_title.setStyleSheet(default_style)
        self.input_publisher.setStyleSheet(default_style)
        self.input_edition.setStyleSheet(default_style)
        self.input_stock.setStyleSheet(default_style)

        # MAC-FIX: Für Fehler-Felder auch!
        error_style = f"background-color: #FFFFFF; color: #000000; border: 2px solid #D32F2F; border-radius: {BUTTON_RADIUS}px; padding: 10px;"

        ok = True
        if not isbn:
            self.input_isbn.setStyleSheet(error_style)
            ok = False
        if not t:
            self.input_title.setStyleSheet(error_style)
            ok = False
        if not p:
            self.input_publisher.setStyleSheet(error_style)
            ok = False
        if not e:
            self.input_edition.setStyleSheet(error_style)
            ok = False
        if not s or not s.isdigit():
            self.input_stock.setStyleSheet(error_style)
            ok = False

        if not ok:
            self.error_label.show()
            return

        self.accept()


# ==============================================================================
# Batuhan: BuchverwaltungWidget
# Zweck: Hauptseite der Buchverwaltung
# - Actionbar: Suche + "Sortieren nach" Dropdown + Button "Buch hinzufügen"
# - Tabelle mit Bestand (+/-) und Aktionen (Bearbeiten/Löschen)
# - Suchlogik + Sortierlogik (Titel/Verlag/Auflage)
#
# Refactoring:
# - Das Widget erbt jetzt von BasePageWidget.
# - Header, Breadcrumb, Seitentitel und Footer werden nicht mehr lokal
#   aufgebaut, sondern zentral bereitgestellt.
# - Der eigentliche Seiteninhalt wird nur noch in self.content_layout eingefügt.
# ==============================================================================
class BuchverwaltungWidget(BasePageWidget):
    COLOR = "#5CB1D6"

    def __init__(self, parent=None):
        super().__init__(
            breadcrumb_text="Startseite > Hauptmenü > Buchverwaltung",
            page_title="Bücherverwaltung",
            accent_color=self.COLOR,
            parent=parent
        )

        self.db_manager = DatabaseManager()  # Initialisiert den Datenbank-Motor by René, Georg, Denis

        # ---------------------------
        # Layout-Grundstruktur
        # Hinweis:
        # - Header/Breadcrumb/Footer werden jetzt zentral von BasePageWidget
        #   erzeugt und müssen hier nicht mehr separat erstellt werden.
        # ---------------------------

        # ================= ACTION BAR =================
        # Suche + Sortieren-nach Dropdown + Button "Buch hinzufügen"
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 5)
        action_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(input_style(self.COLOR))
        action_layout.addWidget(self.search_input)

        # >>> ÄNDERUNG: statt Verlag-Filter jetzt Sortierungsauswahl <<<
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sortieren nach: ISBN", "Titel", "Verlag", "Auflage"])
        self.sort_combo.setFixedWidth(200)
        self.sort_combo.setStyleSheet(combo_style(self.COLOR))
        action_layout.addWidget(self.sort_combo)

        action_layout.addStretch()

        self.btn_add = QPushButton("➕ Buch hinzufügen")
        self.btn_add.setStyleSheet(primary_button_style(self.COLOR))
        self.btn_add.clicked.connect(self.open_book_dialog)
        action_layout.addWidget(self.btn_add)

        self.content_layout.addLayout(action_layout)

        # ================= TABLE =================
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ISBN", "Titel", "Verlag", "Auflage", "Bestand", "Aktionen"])
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                alternate-background-color: #F9F9F9;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                gridline-color: #EDEDED;
                font-size: 15px;
                color: #000000;
            }}
            QHeaderView::section {{
                background-color: #F0F0F0;
                color: #000000;
                font-weight: bold;
                border: none;
                border-bottom: 3px solid {self.COLOR};
                padding: 12px;
            }}
        """)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ISBN
        self.table.setColumnWidth(0, 160)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Titel
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Verlag

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Auflage
        self.table.setColumnWidth(3, 120)

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Bestand
        self.table.setColumnWidth(4, 180)

        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Aktionen
        self.table.setColumnWidth(5, 150)

        # René Bezold, Georg Zinn:
        # Lade-Widget, damit nicht sofort die leere Tabelle angezeigt wird
        # (sondern erst "Daten werden geladen" + Spinner)
        self.data_stack = LoadingTableStack(self.table, retry_callback=self.filter_table)
        self.content_layout.addWidget(self.data_stack)

        # Signale: bei Änderungen sofort aktualisieren (Suche + Sortierung)
        self.search_input.textChanged.connect(self.filter_table)
        self.sort_combo.currentTextChanged.connect(self.filter_table)

    # --------------------------------------------------------------------------
    # Tabelle befüllen (0..3 normale Items, 4/5 Widgets)
    # --------------------------------------------------------------------------
    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        for row, book in enumerate(data_list):
            for col in range(4):
                item = QTableWidgetItem(str(book[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if col in [0, 3]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            self._set_stock_widget(row, book[0], int(book[4]))
            self._set_actions_widget(row, book[0])

    # --------------------------------------------------------------------------
    # Bestand-Widget (– Zahl +)
    # --------------------------------------------------------------------------
    def _set_stock_widget(self, row, isbn, stock):
        bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

        stock_widget = QWidget()
        stock_widget.setStyleSheet(f"background-color: {bg_color};")

        layout = QHBoxLayout(stock_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_minus = QPushButton("–")
        btn_minus.setFixedSize(35, 35)
        btn_minus.setStyleSheet(stock_button_style())

        lbl_stock = QLabel(str(stock))
        lbl_stock.setFixedWidth(50)
        lbl_stock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_stock.setStyleSheet("font-size: 15px; font-weight: bold; color: #000000; background: transparent;")

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(35, 35)
        btn_plus.setStyleSheet(stock_button_style())

        btn_minus.clicked.connect(lambda ch, x=isbn: self.change_stock(x, -1))
        btn_plus.clicked.connect(lambda ch, x=isbn: self.change_stock(x, +1))

        layout.addWidget(btn_minus)
        layout.addWidget(lbl_stock)
        layout.addWidget(btn_plus)

        self.table.setCellWidget(row, 4, stock_widget)

    # --------------------------------------------------------------------------
    # Aktionen-Widget (Bearbeiten/Löschen)
    # --------------------------------------------------------------------------
    def _set_actions_widget(self, row, isbn):
        bg_color = "#F9F9F9" if row % 2 != 0 else "#FFFFFF"

        action_widget = QWidget()
        action_widget.setStyleSheet(f"background-color: {bg_color};")

        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 0, 5, 0)
        action_layout.setSpacing(15)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(45, 45)
        btn_edit.setStyleSheet(icon_button_style("#E0E0E0"))
        btn_edit.clicked.connect(lambda ch, x=isbn: self.edit_book(x))

        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(45, 45)
        btn_delete.setStyleSheet(icon_button_style("#FFCDD2"))
        btn_delete.clicked.connect(lambda ch, x=isbn: self.delete_book(x))

        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_delete)

        self.table.setCellWidget(row, 5, action_widget)

    # --------------------------------------------------------------------------
    # Daten werden direkt in die MariaDB geschrieben
    # --------------------------------------------------------------------------
    def open_book_dialog(self):
        d = BookDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            try:
                # Wir schicken die Daten direkt an den Datenbank-Manager
                self.db_manager.add_book(
                    d.input_isbn.text().strip(),
                    d.input_title.text().strip(),
                    d.input_publisher.text().strip(),
                    d.input_edition.text().strip(),
                    int(d.input_stock.text().strip())
                )
                # Tabelle neu laden, um das neue Buch anzuzeigen
                self.filter_table()
            except Exception as e:
                # Falls z.B. die ISBN schon existiert, zeigt das Loading-Widget den Fehler
                self.data_stack.show_error(f"Fehler beim Hinzufügen: {str(e)}")

    # --------------------------------------------------------------------------
    # Ändern der aktuellen Werte direkt aus der UI-Tabelle
    # --------------------------------------------------------------------------
    def edit_book(self, isbn):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == isbn:
                book_data = (
                    isbn,
                    self.table.item(row, 1).text(),
                    self.table.item(row, 2).text(),
                    self.table.item(row, 3).text(),
                    int(self.table.cellWidget(row, 4).findChild(QLabel).text())
                )

                d = BookDialog(self, book_data=book_data)
                if d.exec() == QDialog.DialogCode.Accepted:
                    try:
                        t = d.input_title.text().strip()
                        p = d.input_publisher.text().strip()
                        e = d.input_edition.text().strip()
                        s = int(d.input_stock.text().strip())

                        self.db_manager.update_book(isbn, t, p, e, s)

                        self.filter_table()
                    except Exception as e:
                        self.data_stack.show_error(f"Fehler beim Speichern: {str(e)}")
                break

    # --------------------------------------------------------------------------
    # Physisches Löschen aus der MariaDB
    # --------------------------------------------------------------------------
    def delete_book(self, isbn):
        confirm = DeleteConfirmDialog(self)
        if confirm.exec() == QDialog.DialogCode.Accepted:
            try:
                self.db_manager.delete_book(isbn)

                self.filter_table()
            except Exception as e:
                self.data_stack.show_error(f"Löschfehler: {str(e)}")

    # --------------------------------------------------------------------------
    # Bestand ändern (plus/minus) - Überarbeitet für Datenbank-Anbindung
    # --------------------------------------------------------------------------
    def change_stock(self, isbn, delta):
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).text() == isbn:
                    stock_widget = self.table.cellWidget(row, 4)
                    lbl = stock_widget.findChild(QLabel)
                    current_stock = int(lbl.text())

                    new_stock = max(0, current_stock + delta)

                    self.db_manager.update_stock(isbn, new_stock)

                    # Tabelle neu laden, um den aktuellen Stand vom Server zu zeigen
                    self.filter_table()
                    break
        except Exception as e:
            # Fehlerbehandlung, falls der Raspberry Pi nicht antwortet
            self.data_stack.show_error(f"Bestand-Update fehlgeschlagen: {str(e)}")

    # René Bezold, Georg Zinn:
    # Filter- und Sortierlogik mit Ladeanimation + Fehlerbehandlung
    def filter_table(self):
        self.data_stack.show_loading()
        self._execute_filter()

    # René Bezold, Georg Zinn:
    # Filter- und Sortierlogik mit Ladeanimation + Fehlerbehandlung
    def _execute_filter(self):
        try:
            # 1. Suchtext und Sortierung aus der GUI holen
            txt = self.search_input.text().strip()
            sort_opt = self.sort_combo.currentText()

            # 2. Datenbank-Abfrage starten
            results = self.db_manager.get_books(txt, sort_opt)

            # 3. Daten in Tabelle laden
            self.load_table_data(results)

            # 4. Umschalten auf die Tabelle
            self.data_stack.show_table()

        except Exception as e:
            # Fehlerfall (z.B. Raspberry Pi offline)
            self.data_stack.show_error(f"Datenbankfehler: {str(e)}")

    def showEvent(self, event):
        super().showEvent(event)
        # Ruft die bestehende Lade-Logik auf
        self.filter_table()