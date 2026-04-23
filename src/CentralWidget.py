# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: CentralWidget (GUI Design)
# Autoren: Daniel Popp und Mustafa Demiral
# Stand: GUI mit Original-Farben und korrigierten Variablen + Info Button
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (QWidget, QPushButton, QGridLayout, QVBoxLayout,
                             QLabel, QHBoxLayout, QSizePolicy, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from app_paths import resource_path_any


# ==============================================================================
# Info Dialog (Pop-Up für Software-Infos, Entwickler und Etiketten)
# ==============================================================================
class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Info & Version")
        self.setFixedSize(450, 340)

        # Zwingt den Dialog auf weißen Hintergrund
        self.setStyleSheet("""
            QDialog { 
                background-color: #FFFFFF; 
            }
            QLabel { 
                color: #000000; 
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        info_text = (
            "<b style='font-size: 16px; color: #000000;'>BooktrackQR Version 1.0</b><br><br>"
            "<span style='color: #000000; font-size: 14px;'>"
            "Software zur Verwaltung der Bücher in den Technikerschulen.<br><br>"
            "<b>Entwickler Team im Schuljahr 25/26:</b><br>"
            "FSWI-2<br>"
            "<i>Batuhan Aktürk, Daniel Popp, Jaclyn Barta, Mustafa Demiral, "
            "Ahmet Toplar, Harun Kayaci, René Bezold, Georg Zinn, Denis Sukkau</i><br><br>"
            "<b>Zum Drucken der QR-Codes bitte folgende Etiketten verwenden:</b>"
            "</span>"
        )
        lbl_info = QLabel(info_text)
        lbl_info.setTextFormat(Qt.TextFormat.RichText)
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        link_text = (
            "<a href='https://www.bueromarkt-ag.de/inkjet-etiketten_herma_8831_special_weiss,p-8831.html' "
            "style='color: #0056b3; text-decoration: underline; font-size: 14px; font-weight: bold;'>"
            "Herma Inkjet-Etiketten 8831 Special, 25,4 x 25,4mm</a>"
        )
        lbl_link = QLabel(link_text)
        lbl_link.setOpenExternalLinks(True)
        lbl_link.setWordWrap(True)
        layout.addWidget(lbl_link)

        layout.addStretch()

        btn_close = QPushButton("Schließen")
        btn_close.setFixedSize(140, 40)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 2px solid #999999;
            }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


# ==============================================================================
# CentralWidget
# ==============================================================================
class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)

        # Daniel: Grundlegendes Setup und Design
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()

        # --- HEADER BEREICH ---
        header_layout = QHBoxLayout()

        # 1. Container links (ersetzt dummy_left, behält aber 200px Breite für die Zentrierung)
        left_container = QWidget()
        left_container.setFixedWidth(200)
        left_container.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # --- NEU: Info Button ---
        self.btn_info = QPushButton("Info")
        self.btn_info.setFixedSize(70, 35)
        self.btn_info.setToolTip("Informationen & Etiketten")
        self.btn_info.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #333333;
                border: 2px solid #D9DDE3;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border: 2px solid #333333;
            }
        """)
        self.btn_info.clicked.connect(self.show_info_dialog)

        left_layout.addWidget(self.btn_info, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        left_layout.addStretch()

        header_layout.addWidget(left_container)

        # Mustafa: Header Elemente (Titel & Logo)
        # 2. Titel (Mitte)
        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # 3. Schullogo (Rechts)
        logo_label = QLabel()
        logo_path = self.get_image_path("technikerschule_logo.png")
        pixmap = QPixmap(logo_path)

        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

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

        # Mustafa: Button Konfiguration mit DEINEN ORIGINALFARBEN
        buttons_config = [
            ("AUSLEIHE", "icon_ausleihe.png", "#8DBF42", 0, 0, "btn_ausleihe"),
            ("RÜCKGABE", "icon_rueckgabe.png", "#E57368", 0, 1, "btn_rueckgabe"),
            ("BUCHVERWALTUNG", "icon_buch.png", "#5CB1D6", 1, 0, "btn_bestand"),
            ("SCHÜLERVERWALTUNG", "icon_user.png", "#F1BD4D", 1, 1, "btn_schueler"),
        ]

        for text, img_name, color, row, col, attr_name in buttons_config:
            full_img_path = self.get_image_path(img_name)
            btn = self.create_centered_button(text, full_img_path, color)
            setattr(self, attr_name, btn)
            grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)
        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)

    def get_image_path(self, filename):
        return resource_path_any(os.path.join("pic", filename), os.path.join("..", "pic", filename))

    def create_centered_button(self, text, icon_path, color):
        btn = QPushButton()
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumSize(250, 180)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(10, 50, 10, 20)
        btn_layout.setSpacing(15)

        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none;")
        btn_layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setFont(QFont("Open Sans", 16, QFont.Weight.Bold))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: white; background-color: transparent; border: none;")
        btn_layout.addWidget(text_label)

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

    # --- NEU: Funktion zum Öffnen des Info-Dialogs ---
    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()