# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: loading_widgets.py
# Autoren: René Bezold, Denis Sukkau, Georg Zinn
# Zweck: Wiederverwendbare Lade- und Fehleranzeige für Tabellen (User Story: Resilienz)
# ------------------------------------------------------------------------------

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QProgressBar, QPushButton, QLabel, QWidget
from PyQt6.QtCore import Qt


class LoadingTableStack(QStackedWidget):
    """
    Ein Container, der zwischen der Datentabelle, einem Lade-Screen
    und einer Fehlermeldung umschalten kann.
    """

    def __init__(self, table_widget, retry_callback, parent=None):
        super().__init__(parent)
        self.table = table_widget
        self.retry_callback = retry_callback

        # SEITE 0: Die eigentliche Tabelle
        self.addWidget(self.table)

        # SEITE 1: Lade-Screen (Progress-Indikator)
        self.loading_screen = QWidget()
        l_layout = QVBoxLayout(self.loading_screen)
        l_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # "Endlos"-Ladebalken für unbestimmte Zeit
        self.progress.setFixedWidth(350)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
                height: 15px;
                background: #F9F9F9;
            }
            QProgressBar::chunk {
                background-color: #F1BD4D; /* Euer Gelbton aus der Verwaltung */
                width: 30px;
                border-radius: 3px;
            }
        """)

        l_text = QLabel("⏳ Daten werden vom Raspberry Pi geladen...")
        l_text.setStyleSheet("font-size: 16px; color: #333333; margin-bottom: 10px; font-weight: bold;")

        l_layout.addWidget(l_text)
        l_layout.addWidget(self.progress)
        self.addWidget(self.loading_screen)

        # SEITE 2: Fehler-Screen (Retry-Option)
        self.error_screen = QWidget()
        e_layout = QVBoxLayout(self.error_screen)
        e_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.error_msg = QLabel("⚠️ Verbindung zum MariaDB-Server unterbrochen!")
        self.error_msg.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 16px; margin-bottom: 15px;")

        self.btn_retry = QPushButton("🔄 Erneut versuchen")
        self.btn_retry.setFixedWidth(220)
        self.btn_retry.setCursor(Qt.CursorShape.PointingHandCursor)

        # Nutzt euren gelben Button-Style passend zur Verwaltung
        self.btn_retry.setStyleSheet("""
            QPushButton { 
                background-color: #F1BD4D; 
                color: white; 
                padding: 10px;
                border: none;
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:hover { 
                background-color: #e5b03d;
                border: 2px solid #333333; 
            }
        """)

        # Signal-Verknüpfung: Ruft die Lade-Funktion im entsprechenden Tab auf
        self.btn_retry.clicked.connect(self.retry_callback)

        e_layout.addWidget(self.error_msg)
        e_layout.addWidget(self.btn_retry)
        self.addWidget(self.error_screen)

    # Hilfsmethoden zur Steuerung der Ansicht
    def show_loading(self):
        self.setCurrentIndex(1)

    def show_table(self):
        self.setCurrentIndex(0)

    def show_error(self, message=None):
        if message:
            self.error_msg.setText(f"⚠️ {message}")
        self.setCurrentIndex(2)