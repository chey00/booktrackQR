# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: CentralWidget (GUI Design)
# Autoren: Daniel Popp, Mustafa Demiral
# Stand: GUI ohne Logik
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (QWidget, QPushButton, QGridLayout, QVBoxLayout,
                             QLabel, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)

        # Daniel: Grundlegendes Setup und Design
        # WICHTIG: Damit der weiße Hintergrund gezeichnet wird!
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Hauptlayout (Vertikal)
        main_layout = QVBoxLayout()

        # --- HEADER BEREICH ---
        header_layout = QHBoxLayout()

        # 1. Unsichtbares Gegengewicht (Links) - Feste Breite für Zentrierung
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        dummy_left.setStyleSheet("background: transparent;")
        header_layout.addWidget(dummy_left)

        # Mustafa: Header Elemente (Titel & Logo)
        # 2. Titel (Mitte)
        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))  # Open Sans wie das Schullogo
        title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # 3. Schullogo (Rechts)
        logo_label = QLabel()
        # Pfad dynamisch ermitteln (verhindert Fehler auf Mac/Windows)
        logo_path = self.get_image_path("technikerschule_logo.png")
        pixmap = QPixmap(logo_path)

        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("Logo nicht gefunden")

        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        logo_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Daniel: Breadcrumb Navigation
        self.back_label = QLabel("Startseite > Hauptmenü")
        self.back_label.setStyleSheet(
            "color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px; background: transparent;")
        main_layout.addWidget(self.back_label)

        # --- BUTTON GRID ---
        grid = QGridLayout()
        grid.setSpacing(25)

        # Mustafa: Button Konfiguration
        # Liste der Buttons: (Text, Bildname, Farbe, Zeile, Spalte)
        buttons_config = [
            ("AUSLEIHE", "icon_ausleihe.png", "#8DBF42", 0, 0), #https://www.flaticon.com/free-icon-font/book-plus_15399184?k=1770709197884
            ("RÜCKGABE", "icon_rueckgabe.png", "#E57368", 0, 1), #https://www.flaticon.com/free-icon-font/guide-alt_15399213?page=1&position=96&term=book&origin=search&related_id=15399213
            ("BUCHVERWALTUNG", "icon_buch.png", "#5CB1D6", 1, 0), #https://www.flaticon.com/free-icon-font/book-circle-arrow-up_9585307?term=book+arrow&related_id=9585307
            ("SCHÜLERVERWALTUNG", "icon_user.png", "#F1BD4D", 1, 1), #https://www.flaticon.com/free-icon-font/user-gear_9844201
        ]

        # Daniel: Erstellung der Buttons im Grid
        for text, img_name, color, row, col in buttons_config:
            # Vollen Pfad zum Bild holen
            full_img_path = self.get_image_path(img_name)

            # Button erstellen (nur Visualisierung, keine Logik/Connect)
            btn = self.create_centered_button(text, full_img_path, color)

            grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)
        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)

    def get_image_path(self, filename):
        """
        Hilfsfunktion: Findet den Pfad zum 'pic' Ordner, egal von wo man startet.
        Geht davon aus, dass die Ordnerstruktur so ist:
        /Projekt/src/CentralWidget.py
        /Projekt/pic/bild.png
        """
        base_dir = os.path.dirname(__file__)  # Ordner dieser Datei (src)
        return os.path.join(base_dir, "..", "pic", filename)

    def create_centered_button(self, text, icon_path, color):
        """
        Erstellt das Design für einen Button mit Icon oben und Text unten.
        """
        btn = QPushButton()
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumSize(250, 180)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Internes Layout
        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(10, 50, 10, 20)
        btn_layout.setSpacing(15)

        # Icon
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none;")
        btn_layout.addWidget(icon_label)

        # Text
        text_label = QLabel(text)
        text_label.setFont(QFont("Open Sans", 16, QFont.Weight.Bold))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Text explizit weiß setzen
        text_label.setStyleSheet("color: white; background-color: transparent; border: none;")
        btn_layout.addWidget(text_label)

        # Button Styling
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover {{
                border: 3px solid #333333; 
            }}
            QPushButton:pressed {{
                background-color: #444444;
            }}
        """)

        return btn
