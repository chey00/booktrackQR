#
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from app_paths import resource_path_any


class BasePageWidget(QWidget):
    """
    Gemeinsame Basisklasse für alle Hauptseiten.

    Stellt zentral bereit:
    - Header mit App-Titel und Logo
    - Breadcrumb
    - Seitentitel
    - gemeinsamen Inhaltsbereich
    - gemeinsamen Footer mit Zurück-Button
    """

    BUTTON_RADIUS = 10

    def __init__(self, breadcrumb_text: str, page_title: str, accent_color: str, parent=None):
        super().__init__(parent)

        self.accent_color = accent_color

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #F7F8FA;")

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(40, 25, 40, 25)
        self.root_layout.setSpacing(16)

        # ================= HEADER =================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        dummy_left = QWidget()
        dummy_left.setFixedWidth(200)
        header_layout.addWidget(dummy_left)

        self.title_label = QLabel("BooktrackQR")
        self.title_label.setFont(QFont("Open Sans", 42, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #333333; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.title_label)

        self.logo_label = QLabel()
        logo_path = resource_path_any(
            os.path.join("pic", "technikerschule_logo.png"),
            os.path.join("..", "pic", "technikerschule_logo.png")
        )
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(
                    200, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        self.logo_label.setFixedWidth(200)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.logo_label)

        self.root_layout.addLayout(header_layout)

        # ================= BREADCRUMB =================
        self.breadcrumb_label = QLabel(breadcrumb_text)
        self.breadcrumb_label.setStyleSheet(
            "color: #666666; font-style: italic; font-size: 13px; margin-left: 6px;"
        )
        self.root_layout.addWidget(self.breadcrumb_label)

        # ================= PAGE TITLE =================
        self.page_title_label = QLabel(page_title)
        self.page_title_label.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        self.page_title_label.setStyleSheet(
            f"color: {self.accent_color}; margin-left: 6px; margin-bottom: 4px;"
        )
        self.root_layout.addWidget(self.page_title_label)

        # ================= CONTENT CARD =================
        self.content_card = QWidget()
        self.content_card.setObjectName("ContentCard")
        self.content_card.setStyleSheet(f"""
            QWidget#ContentCard {{
                background-color: #FFFFFF;
                border: 1px solid #E3E6EA;
                border-radius: 16px;
            }}
        """)

        self.content_layout = QVBoxLayout(self.content_card)
        self.content_layout.setContentsMargins(24, 24, 24, 20)
        self.content_layout.setSpacing(16)

        self.root_layout.addWidget(self.content_card, 1)

        # ================= FOOTER =================
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(self.get_primary_button_style())
        self.btn_back.setMinimumHeight(44)
        footer_layout.addWidget(self.btn_back)

        self.root_layout.addLayout(footer_layout)

    def get_primary_button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                padding: 10px 22px;
                border: 3px solid {self.accent_color};
                border-radius: {self.BUTTON_RADIUS}px;
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

    def get_secondary_button_style(self):
        return f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #333333;
                padding: 10px 22px;
                border: 2px solid #D9DDE3;
                border-radius: {self.BUTTON_RADIUS}px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border: 2px solid #333333;
                background-color: #F7F7F7;
            }}
            QPushButton:pressed {{
                background-color: #ECECEC;
            }}
        """

    def get_neutral_button_style(self):
        return f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #333333;
                padding: 10px 22px;
                border: 3px solid #E0E0E0;
                border-radius: {self.BUTTON_RADIUS}px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border: 3px solid #333333;
            }}
            QPushButton:pressed {{
                background-color: #444444;
                border: 3px solid #444444;
                color: white;
            }}
        """

    def set_breadcrumb(self, text: str):
        self.breadcrumb_label.setText(text)

    def set_page_title(self, text: str):
        self.page_title_label.setText(text)

