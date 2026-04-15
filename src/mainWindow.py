# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: MainWindow (GUI)
#
# Autoren: Mustafa Demiral, Ahmet Toplar, Harun Kayaci, Daniel Popp, Batuhan Aktürk, René Bezold, Georg Zinn
# Stand: GUI mit Logik (Inklusive Buchverwaltung/Bestand)
# ------------------------------------------------------------------------------

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject, QThread

from database_manager import DatabaseManager
from CentralWidget import CentralWidget
from schuelerverwaltung import SchuelerverwaltungWidget
from Rueckgabe import RueckgabeWidget
from Buchverwaltung import BuchverwaltungWidget  # Harun Kayaci
from Ausleihe import AusleiheWidget  # Batuhan Aktürk & Daniel Popp


class _HeartbeatWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(bool, str, str)  # ist_online, user_msg, tech_msg

    def __init__(self, db_config):
        super().__init__()
        self._db_config = db_config
        self.db_manager = DatabaseManager()
        self.error_overlay = None

    # René Bezold, Georg Zinn: Worker-Thread für Heartbeat-Check (Verbindungsprüfung)
    def run(self):
        try:
            from loading_gate import check_db_connection
            ist_online, user_msg, tech_msg = check_db_connection(self._db_config)
        except Exception as e:
            ist_online = False
            user_msg = "Unbekannter Fehler beim Verbindungscheck."
            tech_msg = repr(e)
        self.result.emit(ist_online, user_msg, tech_msg)
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, db_config, parent=None):  # db_config hinzugefügt René Bezold, Georg Zinn
        super(MainWindow, self).__init__(parent)

        # René Bezold
        self.db_config = db_config
        self.db_manager = DatabaseManager()
        self.error_overlay = None
        # -----------------------------------------

        self.setWindowTitle("BooktrackQR")
        self.setMinimumSize(950, 750)
        self.setStyleSheet("QMainWindow { background-color: white; }")

        # Ahmet
        # 1. Den "Kartenstapel" erstellen
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # 2. Deine erstellten Bildschirme laden
        self.main_menu_widget = CentralWidget(self)
        self.schueler_widget = SchuelerverwaltungWidget(self)
        self.rueckgabe_widget = RueckgabeWidget(self)
        self.bestand_widget = BuchverwaltungWidget(self)  # Harun Kayaci
        self.ausleihe_widget = AusleiheWidget(self)  # Batuhan Aktürk & Daniel Popp

        # Mustafa
        # 3. Bildschirme zum Stapel hinzufügen
        self.stacked_widget.addWidget(self.main_menu_widget)  # Index 0
        self.stacked_widget.addWidget(self.schueler_widget)  # Index 1
        self.stacked_widget.addWidget(self.rueckgabe_widget)  # Index 2
        self.stacked_widget.addWidget(self.bestand_widget)  # Index 3
        self.stacked_widget.addWidget(self.ausleihe_widget)  # Index 4

        # 4. Den Button aus dem Hauptmenü mit der Wechsel-Funktion verbinden
        self.main_menu_widget.btn_schueler.clicked.connect(self.zeige_schuelerverwaltung)
        self.main_menu_widget.btn_rueckgabe.clicked.connect(self.zeige_rueckgabe)
        self.main_menu_widget.btn_bestand.clicked.connect(self.zeige_bestand)  # Verbindung für Bestand Harun Kayaci
        self.main_menu_widget.btn_ausleihe.clicked.connect(self.zeige_ausleihe)  # Batuhan Aktürk & Daniel Popp

        # Ahmet
        # Zurück -> Hauptmenü
        self.schueler_widget.btn_back.clicked.connect(self.zeige_hauptmenue)
        self.rueckgabe_widget.btn_back.clicked.connect(self.zeige_hauptmenue)
        self.bestand_widget.btn_back.clicked.connect(self.zeige_hauptmenue)
        self.ausleihe_widget.btn_back.clicked.connect(self.zeige_hauptmenue)

        # René Bezold, Georg Zinn: Thread/Worker-Status für Heartbeat
        self._hb_thread = None
        self._hb_worker = None
        self._hb_running = False

        # René Bezold, Georg Zinn Start des Watchdogs
        self.db_watchdog = QTimer(self)
        self.db_watchdog.setInterval(10000)
        self.db_watchdog.timeout.connect(self.check_heartbeat)
        self.db_watchdog.start()
        # -------------------------------------------------

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

    # René Bezold, Georg Zinn
    def check_heartbeat(self):
        """Prüft im Hintergrund, ob der Pi noch da ist (nicht-blockierend für die GUI)."""
        if self._hb_running:
            return  # verhindert parallele Checks, falls ein Check hängt/noch läuft

        self._hb_running = True

        self._hb_thread = QThread(self)
        self._hb_worker = _HeartbeatWorker(self.db_config)
        self._hb_worker.moveToThread(self._hb_thread)

        self._hb_thread.started.connect(self._hb_worker.run)
        self._hb_worker.result.connect(self._on_heartbeat_result)
        self._hb_worker.finished.connect(self._hb_thread.quit)
        self._hb_worker.finished.connect(self._hb_worker.deleteLater)
        self._hb_thread.finished.connect(self._hb_thread.deleteLater)
        self._hb_thread.finished.connect(self._on_heartbeat_finished)

        self._hb_thread.start()

    def _on_heartbeat_result(self, ist_online: bool, user_msg: str, tech_msg: str):
        if not ist_online:
            self.show_db_down_gui(user_msg)

    def _on_heartbeat_finished(self):
        self._hb_running = False
        self._hb_thread = None
        self._hb_worker = None

    # René Bezold, Georg Zinn
    def show_db_down_gui(self, fehler):
        """Erzeugt ein Fullscreen-Overlay, wenn der Server weg ist."""
        if self.error_overlay:
            return
        self.db_watchdog.stop()
        self.error_overlay = QWidget(self)
        self.error_overlay.setGeometry(0, 0, self.width(), self.height())
        self.error_overlay.setStyleSheet("background-color: #0b1220;")

        layout = QVBoxLayout(self.error_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg_label = QLabel(f"⚠️ VERBINDUNG VERLOREN\n\nDer Server (Raspberry Pi) ist offline.\n({fehler})")
        msg_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        retry_btn = QPushButton("Neu verbinden")
        retry_btn.setFixedSize(200, 40)
        retry_btn.setStyleSheet("background: #8ea9ff; color: #0b1220; font-weight: bold; border-radius: 8px;")
        retry_btn.clicked.connect(self.try_reconnect)

        layout.addWidget(msg_label)
        layout.addSpacing(20)
        layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.error_overlay.show()
        self.error_overlay.raise_()

    # René Bezold, Georg Zinn
    def try_reconnect(self):
        """Prüft, ob der Pi wieder an ist."""
        from loading_gate import check_db_connection
        ok, _, _ = check_db_connection(self.db_config)
        if ok:
            if self.error_overlay:
                self.error_overlay.deleteLater()
                self.error_overlay = None
            self.db_watchdog.start()

    # René Bezold, Georg Zinn
    def resizeEvent(self, event):
        """Sorgt dafür, dass das Fehler-GUI beim Skalieren mitwächst."""
        if self.error_overlay:
            self.error_overlay.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
