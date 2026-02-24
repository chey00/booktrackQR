# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (GUI Design & Validierungs-Logik)
# Autoren: Jaclyn Barta
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class RueckgabeWidget(QWidget):
    """
    Widget zum Scannen von Büchern bzw. QR-Code.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Jaclyn: Hintergrund-Setup
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Das Hauptlayout des gesamten Widgets
        main_layout = QVBoxLayout()

        # === HEADER (Identisch mit Hauptmenü) ===
        header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "pic", "technikerschule_logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setFixedWidth(200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Jaclyn: Breadcrumbs
        self.back_label = QLabel("Startseite > Hauptmenü > Rückgabe")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px;")
        main_layout.addWidget(self.back_label)

        # Titel mit Farbcode #E57368
        page_title = QLabel("Rückgabe")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #E57368; margin-left: 10px;")
        main_layout.addWidget(page_title)

        main_layout.addSpacing(20)

        # --- DAS GRAUE FELD (Kamera-Bereich kleiner gemacht) ---
        self.kamera_box = QWidget()
        self.kamera_box.setStyleSheet("background-color: #F9F9F9; border: 2px solid #E0E0E0; border-radius: 10px;")
        self.kamera_box.setFixedHeight(300)  # Höhe von 400 auf 300 reduziert

        # Internes Layout für den Text in der Box
        box_layout = QVBoxLayout(self.kamera_box)
        text_label = QLabel("📷 Kamera wird gestartet...\nBitte halten Sie den Buch-QR-Code in das Sichtfeld.")
        text_label.setFont(QFont("Open Sans", 14))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        box_layout.addWidget(text_label)

        # Die Box zum Hauptlayout hinzufügen
        main_layout.addWidget(self.kamera_box)

        # --- ABSTANDSHALTER (Schiebt den Button nach unten) ---
        main_layout.addStretch()

        # --- FOOTER (Button außerhalb der Box) ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()  # Schiebt Button nach rechts

        self.zurueck_btn = QPushButton("⬅ Zurück zum Hauptmenü")
        self.zurueck_btn.setStyleSheet("""
            QPushButton { 
                background-color: #E57368; 
                color: white; 
                padding: 10px 25px; 
                border: 3px solid #E57368; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:hover { 
                border: 3px solid #333333; 
            }
            QPushButton:pressed { 
                background-color: #444444; 
                border: 3px solid #444444; 
            }
        """)

        footer_layout.addWidget(self.zurueck_btn)
        main_layout.addLayout(footer_layout)

        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)