import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from app_paths import resource_path_any


# ==============================================================================
# Info Dialog (Zwingt Styles auf Schwarz/Weiß für maximale Lesbarkeit) Daniel Popp
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

        # 1. Text-Block (Version, Info & Team)
        # Wir nutzen Inline-CSS, um die schwarze Farbe für die Labels zu garantieren
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

        # 2. Der klickbare Link
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

        # 3. Schließen Button (Deutlich sichtbar)
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
# BasePageWidget Daniel Popp
# ==============================================================================
class BasePageWidget(QWidget):
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

        # Container links (200px breit für die Zentrierung des Titels)
        left_container = QWidget()
        left_container.setFixedWidth(200)
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # --- OPTIMIERT: Info Button (Deutlich erkennbar) ---
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

        # Titel (Zentriert)
        self.title_label = QLabel("BooktrackQR")
        self.title_label.setFont(QFont("Open Sans", 42, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #333333; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.title_label)

        # Logo rechts (200px breit)
        self.logo_label = QLabel()
        logo_path = resource_path_any(
            os.path.join("pic", "technikerschule_logo.png"),
            os.path.join("..", "pic", "technikerschule_logo.png")
        )
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logo_label.setPixmap(
                pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        self.logo_label.setFixedWidth(200)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.logo_label)

        self.root_layout.addLayout(header_layout)

        # Restlicher Code (Breadcrumb, Title, Content, Footer) bleibt identisch...
        self.breadcrumb_label = QLabel(breadcrumb_text)
        self.breadcrumb_label.setStyleSheet("color: #666666; font-style: italic; font-size: 13px; margin-left: 6px;")
        self.root_layout.addWidget(self.breadcrumb_label)

        self.page_title_label = QLabel(page_title)
        self.page_title_label.setFont(QFont("Open Sans", 24, QFont.Weight.Bold))
        self.page_title_label.setStyleSheet(f"color: {self.accent_color}; margin-left: 6px; margin-bottom: 4px;")
        self.root_layout.addWidget(self.page_title_label)

        self.content_card = QWidget()
        self.content_card.setObjectName("ContentCard")
        self.content_card.setStyleSheet(
            "QWidget#ContentCard { background-color: #FFFFFF; border: 1px solid #E3E6EA; border-radius: 16px; }")
        self.content_layout = QVBoxLayout(self.content_card)
        self.content_layout.setContentsMargins(24, 24, 24, 20)
        self.content_layout.setSpacing(16)
        self.root_layout.addWidget(self.content_card, 1)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.btn_back = QPushButton("⬅ Zurück zum Hauptmenü")
        self.btn_back.setStyleSheet(self.get_primary_button_style())
        self.btn_back.setMinimumHeight(44)
        footer_layout.addWidget(self.btn_back)
        self.root_layout.addLayout(footer_layout)

    def get_primary_button_style(self):
        return f"QPushButton {{ background-color: {self.accent_color}; color: white; padding: 10px 22px; border: 3px solid {self.accent_color}; border-radius: {self.BUTTON_RADIUS}px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ border: 3px solid #333333; }}"

    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()