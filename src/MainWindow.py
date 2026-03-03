# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: MainWindow (GUI)
# Autoren: Mustafa Demiral, Ahmet Toplar, Harun Kayaci, Daniel Popp, Batuhan Aktürk
# Stand: GUI mit Logik (Inklusive Buchverwaltung/Bestand)
# ------------------------------------------------------------------------------

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from CentralWidget import CentralWidget
from Schuelerverwaltung import SchuelerverwaltungWidget
from Rueckgabe import RueckgabeWidget
from Buchverwaltung import BuchverwaltungWidget  #Harun Kayaci
from Ausleihe import AusleiheWidget # Batuhan Aktürk & Daniel Popp


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
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
        self.schueler_widget = SchuelerverwaltungWidget()
        self.rueckgabe_widget = RueckgabeWidget()
        self.bestand_widget = BuchverwaltungWidget()  # Harun Kayaci
        self.ausleihe_widget = AusleiheWidget() # Batuhan Aktürk & Daniel Popp

        # Mustafa
        # 3. Bildschirme zum Stapel hinzufügen
        self.stacked_widget.addWidget(self.main_menu_widget)  # Index 0
        self.stacked_widget.addWidget(self.schueler_widget)  # Index 1
        self.stacked_widget.addWidget(self.rueckgabe_widget)  # Index 2
        self.stacked_widget.addWidget(self.bestand_widget)  # Index 3 Harun Kayaci
        self.stacked_widget.addWidget(self.ausleihe_widget)  # Index 4 Batuhan Aktürk & Daniel Popp

        # 4. Den Button aus dem Hauptmenü mit der Wechsel-Funktion verbinden
        self.main_menu_widget.btn_schueler.clicked.connect(self.zeige_schuelerverwaltung)
        self.main_menu_widget.btn_rueckgabe.clicked.connect(self.zeige_rueckgabe)
        self.main_menu_widget.btn_bestand.clicked.connect(self.zeige_bestand)  # Verbindung für Bestand Harun Kayaci
        self.main_menu_widget.btn_ausleihe.clicked.connect(self.zeige_ausleihe) # Batuhan Aktürk & Daniel Popp

        # Ahmet
        # Zurück -> Hauptmenü
        self.schueler_widget.btn_back.clicked.connect(self.zeige_hauptmenue)
        self.rueckgabe_widget.zurueck_btn.clicked.connect(self.zeige_hauptmenue)
        self.bestand_widget.btn_back.clicked.connect(self.zeige_hauptmenue)  # Zurück-Button Bestand Harun Kayaci
        self.ausleihe_widget.btn_back.clicked.connect(self.zeige_hauptmenue) # Batuhan Aktürk & Daniel Popp

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

    # Harun Kayaci
    def zeige_bestand(self):
        """Wechselt zur Buchverwaltung/Bestand (Index 3)"""
        self.stacked_widget.setCurrentIndex(3)

    # Batuhan Aktürk & Daniel Popp
    def zeige_ausleihe(self):
        """Wechselt zur Ausleihe (Index 4)"""
        self.stacked_widget.setCurrentIndex(4)