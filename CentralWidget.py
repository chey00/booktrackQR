#Skript wurde von Daniel Popp und Mustafa Demiral geschrieben#
from PyQt6.QtWidgets import (QWidget, QPushButton, QGridLayout, QVBoxLayout,
                             QLabel, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

###Skript wurde von Daniel Popp und Mustafa Demiral geschrieben###


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
#Daniel
        # WICHTIG: Damit der Hintergrund gezeichnet wird!
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # 1. FESTES DESIGN (Helles Theme erzwingen)
        # Background Weiß, Text Dunkelgrau
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                color: #333333;
                font-family: Arial;
            }
        """)

        # Hauptlayout (Vertikal)
        main_layout = QVBoxLayout()

        # --- HEADER BEREICH ---
        header_layout = QHBoxLayout()

        # 1. Unsichtbares Gegengewicht (Links) - Feste Breite
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        # Transparent, damit kein weißer Kasten entsteht, falls Styles vererbt werden
        dummy_left.setStyleSheet("background: transparent;")
        header_layout.addWidget(dummy_left)
#Mustafa
        # 2. Titel (Mitte) - Sicherstellen, dass er dunkel ist
        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        # Hier erzwingen wir nochmal explizit die Textfarbe
        title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # 3. Schullogo (Rechts)
        logo_label = QLabel()
        pixmap = QPixmap("pictures/technikerschule_logo.png")
        if not pixmap.isNull():
            # Logo skalieren
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        logo_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
#Daniel
        # --- NAVIGATION / BREADCRUMB ---
        self.back_label = QLabel("Startseite > Hauptmenü")
        self.back_label.setStyleSheet(
            "color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px; background: transparent;")
        main_layout.addWidget(self.back_label)

        # --- BUTTON GRID ---
        grid = QGridLayout()
        grid.setSpacing(25)
#Mustafa
        # Konfiguration
        buttons_config = [
            ("AUSLEIHE", "pictures/icon_ausleihe.png", "#8DBF42", 0, 0), #https://www.flaticon.com/free-icon-font/book-plus_15399184?k=1770709197884
            ("RÜCKGABE", "pictures/icon_rueckgabe.png", "#E57368", 0, 1), #https://www.flaticon.com/free-icon-font/guide-alt_15399213?page=1&position=96&term=book&origin=search&related_id=15399213
            ("BUCHVERWALTUNG", "pictures/icon_buch.png", "#5CB1D6", 1, 0), #https://www.flaticon.com/free-icon-font/book-circle-arrow-up_9585307?term=book+arrow&related_id=9585307
            ("SCHÜLERVERWALTUNG", "pictures/icon_user.png", "#F1BD4D", 1, 1) #https://www.flaticon.com/free-icon-font/user-gear_9844201
        ]
#Daniel
        for text, icon_path, color, row, col in buttons_config:
            btn = self.create_centered_button(text, icon_path, color)
            grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)

        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)

    def create_centered_button(self, text, icon_path, color):
        """
        Erstellt die Buttons.
        """
        btn = QPushButton()
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumSize(250, 180)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout im Button
        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(10, 20, 10, 20)
        btn_layout.setSpacing(15)

        # Icon Label
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Background transparent, damit die Buttonfarbe durchkommt
        icon_label.setStyleSheet("background-color: transparent; border: none;")
        btn_layout.addWidget(icon_label)

        # Text Label
        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # WICHTIG: Text im Button muss WEISS bleiben
        text_label.setStyleSheet("color: white; background-color: transparent; border: none;")
        btn_layout.addWidget(text_label)

        # Styling des Buttons selbst
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color}dd; 
                border: 3px solid #333333; 
            }}
            QPushButton:pressed {{
                background-color: #444444;
            }}
        """)

        return btn