# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: MainWindow (GUI)
# Autoren: Mustafa Demiral, Ahmet Toplar
# Stand: GUI mit Logik (inkl. Rückgabe-Reiter)
# ------------------------------------------------------------------------------

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from CentralWidget import CentralWidget
from Schuelerverwaltung import SchuelerverwaltungWidget
from Rueckgabe import RueckgabeDialog  # Ahmet: Import für das Rückgabe-Widget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle("BooktrackQR")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("QWidget { background-color: white; }")

        # Ahmet: Den "Kartenstapel" erstellen
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # 2. Bildschirme laden
        self.main_menu_widget = CentralWidget()
        self.schueler_widget = SchuelerverwaltungWidget()
        self.rueckgabe_widget = RueckgabeDialog()  # Mustafa: Instanz für Rückgabe

        # 3. Bildschirme zum Stapel hinzufügen
        self.stacked_widget.addWidget(self.main_menu_widget)  # Index 0
        self.stacked_widget.addWidget(self.schueler_widget)  # Index 1
        self.stacked_widget.addWidget(self.rueckgabe_widget)  # Index 2

        # --- Ahmet: Verbindungen (Signale) ---

        # Hauptmenü -> Schülerverwaltung
        self.main_menu_widget.btn_schueler.clicked.connect(self.zeige_schuelerverwaltung)

        # Hauptmenü -> Rückgabe (NEU)
        self.main_menu_widget.btn_rueckgabe.clicked.connect(self.zeige_rueckgabe)

        # Schülerverwaltung -> Hauptmenü
        self.schueler_widget.btn_back.clicked.connect(self.zeige_hauptmenue)

        # Rückgabe -> Hauptmenü (NEU)
        # Hinweis: In Rueckgabe.py muss der Button 'zurueck_btn' für MainWindow erreichbar sein
        self.rueckgabe_widget.zurueck_btn.clicked.connect(self.zeige_hauptmenue)

    # --- Mustafa: Navigations-Logik ---

    def zeige_hauptmenue(self):
        """Wechselt zum Hauptmenü (Index 0)"""
        self.stacked_widget.setCurrentIndex(0)

    def zeige_schuelerverwaltung(self):
        """Wechselt zur Schülerverwaltung (Index 1)"""
        self.stacked_widget.setCurrentIndex(1)

    def zeige_rueckgabe(self):
        """Wechselt zur Rückgabe (Index 2)"""
        self.stacked_widget.setCurrentIndex(2)