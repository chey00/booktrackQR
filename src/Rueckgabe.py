# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: RückgabeWidget (GUI Design & Validierungs-Logik)
# ------------------------------------------------------------------------------

import os
from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


class RueckgabeDialog(QDialog):
    """
    Dialog-Fenster zum Scannen von Büchern bw. QR-Code.
    Enthält die Validierungslogik für Pflichtfelder (Klasse).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rückgabe")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()

        # === HEADER (EXAKT wie Hauptfenster) ===
        header_layout = QHBoxLayout()
        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        dummy_left.setStyleSheet("background: transparent;")
        header_layout.addWidget(dummy_left)

        title_label = QLabel("BooktrackQR")
        title_label.setFont(QFont("Open Sans", 50, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "pic", "technikerschule_logo.png")
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

        # Breadcrumb
        back_label = QLabel("Startseite > Rückgabe")
        back_label.setStyleSheet(
            "color: #666666; font-style: italic; margin-left: 10px; margin-bottom: 10px; background: transparent;")
        main_layout.addWidget(back_label)

        # Kamera-Platzhalter (grau wie Screenshot)
        kamera_widget = QWidget()
        kamera_widget.setStyleSheet("background-color: #E0E0E0; border: 2px dashed #CCCCCC; border-radius: 15px;")
        kamera_widget.setFixedHeight(350)
        kamera_layout = QVBoxLayout(kamera_widget)
        kamera_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Kameravorstellung / Buch-QR scannen")
        text_label.setFont(QFont("Open Sans", 14, QFont.Weight.Bold))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #666666; background: transparent;")
        kamera_layout.addWidget(text_label)

        main_layout.addWidget(kamera_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(30)

        # Zurück-Button (rosa wie Screenshot)
        zurueck_btn = QPushButton("← Zurück")
        zurueck_btn.setStyleSheet("""
             QPushButton {
                 background-color: #F8BBD9; 
                 color: #333333;
                 border-radius: 25px;
                 border: none;
                 padding: 12px 30px;
                 font-size: 16px;
                 font-weight: bold;
             }
             QPushButton:hover {
                 background-color: #F48FB1;
             }
         """)
        zurueck_btn.clicked.connect(self.reject)
        main_layout.addWidget(zurueck_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.setContentsMargins(50, 30, 50, 50)
        self.setLayout(main_layout)

