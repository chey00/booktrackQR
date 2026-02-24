# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: BuchverwaltungWidget (Bestandsverwaltung GUI)
# Autoren: Daniel Popp, Mustafa Demiral
# Stand: Design an Gesamtprojekt angepasst (#5CB1D6)
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QLineEdit, QTableWidget, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class BuchverwaltungWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

        # Hauptlayout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 30, 50, 50)

        # === HEADER ===
        header_layout = QHBoxLayout()

        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background: transparent; border: none;")
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

        self.layout.addLayout(header_layout)
        self.layout.addSpacing(20)

        # === NAVIGATION & TITEL ===
        self.back_label = QLabel("Startseite > Hauptmenü > Bestand")
        self.back_label.setStyleSheet("color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px;")
        self.layout.addWidget(self.back_label)

        page_title = QLabel("Bücherbestand verwalten")
        page_title.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        page_title.setStyleSheet("color: #5CB1D6; margin-left: 10px;")  # BLAUER FARBCODE
        self.layout.addWidget(page_title)

        self.layout.addSpacing(20)

        # === SUCHE & FILTER ===
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nach Buchtitel oder ISBN suchen...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background: #F9F9F9;
            }
            QLineEdit:focus {
                border: 2px solid #5CB1D6;
            }
        """)
        search_layout.addWidget(self.search_input)

        self.btn_search = QPushButton("Suchen")
        self.btn_search.setStyleSheet(self._get_button_style("#5CB1D6"))
        search_layout.addWidget(self.btn_search)

        self.layout.addLayout(search_layout)
        self.layout.addSpacing(20)

        # === TABELLE ===
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ISBN", "Titel", "Autor", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                gridline-color: #F0F0F0;
            }
            QHeaderView::section {
                background-color: #F9F9F9;
                padding: 5px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #E0E0E0;
            }
        """)
        self.layout.addWidget(self.table)

        # === FOOTER (ZURÜCK BUTTON) ===
        self.layout.addStretch()
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(self._get_button_style("#5CB1D6"))

        footer_layout.addWidget(self.btn_back)
        self.layout.addLayout(footer_layout)

    def _get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px 25px;
                border: 3px solid {color};
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border: 3px solid #333333;
            }}
            QPushButton:pressed {{
                background-color: #444444;
                border: 3px solid #444444;
            }}
        """