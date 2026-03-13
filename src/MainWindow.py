# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: MainWindow (GUI)
# Autoren: Mustafa Demiral, Ahmet Toplar
# Stand: GUI mit Logik (Inklusive Buchverwaltung/Bestand)
# ------------------------------------------------------------------------------

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from CentralWidget import CentralWidget
from Schuelerverwaltung import SchuelerverwaltungWidget
from Rueckgabe import RueckgabeWidget
from Buchverwaltung import BuchverwaltungWidget  # Import der Buchverwaltung


class MainWindow(QMainWindow):
    def __init__(self, cfg: dict, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle("BooktrackQR")
        self.setMinimumSize(950, 750)
        self.setStyleSheet("QWidget { background-color: white; }")

        # Ahmet
        # 1. Den "Kartenstapel" erstellen
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # 2. Deine erstellten Bildschirme laden
        self.main_menu_widget = CentralWidget()
        self.schueler_widget = SchuelerverwaltungWidget(cfg)
        self.rueckgabe_widget = RueckgabeWidget()
        self.bestand_widget = BuchverwaltungWidget(cfg)  # Neue Instanz für Bestand

        # Mustafa
        # 3. Bildschirme zum Stapel hinzufügen
        self.stacked_widget.addWidget(self.main_menu_widget)  # Index 0
        self.stacked_widget.addWidget(self.schueler_widget)  # Index 1
        self.stacked_widget.addWidget(self.rueckgabe_widget)  # Index 2
        self.stacked_widget.addWidget(self.bestand_widget)  # Index 3

        # 4. Den Button aus dem Hauptmenü mit der Wechsel-Funktion verbinden
        self.main_menu_widget.btn_schueler.clicked.connect(self.zeige_schuelerverwaltung)
        self.main_menu_widget.btn_rueckgabe.clicked.connect(self.zeige_rueckgabe)
        self.main_menu_widget.btn_bestand.clicked.connect(self.zeige_bestand)  # Verbindung für Bestand

        # Ahmet
        # Zurück -> Hauptmenü
        self.schueler_widget.btn_back.clicked.connect(self.zeige_hauptmenue)
        self.rueckgabe_widget.zurueck_btn.clicked.connect(self.zeige_hauptmenue)
        self.bestand_widget.btn_back.clicked.connect(self.zeige_hauptmenue)  # Zurück-Button Bestand

    # Mustafa
    def zeige_hauptmenue(self):
        """Wechselt zum Hauptmenü (Index 0)"""
        self.stacked_widget.setCurrentIndex(0)

    def zeige_schuelerverwaltung(self):
        """Wechselt zur Schülerverwaltung (Index 1)"""
        self.stacked_widget.setCurrentIndex(1)

    def zeige_rueckgabe(self):
        """Wechselt zur Rückgabe (Index 2)"""
        self.stacked_widget.setCurrentIndex(2)

    def zeige_bestand(self):
        """Wechselt zur Buchverwaltung/Bestand (Index 3)"""
        self.stacked_widget.setCurrentIndex(3)
