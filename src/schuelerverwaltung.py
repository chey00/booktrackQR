# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: Gesamte Verwaltung (Schüler, Klassen, Schuljahre, Buchlisten)
# Sprint 2 Autoren: Mustafa Demiral, Ahmet Toplar
# Sprint 3 Autoren: Mustafa Demiral, Luis Overrath
# Sprint 4 Autor: Mustafa Demiral (Dynamische ID-Kalkulation, Mac-Design-Fixes)
# Sprint 5 Autor: Mustafa Demiral (Soft-Delete & Admin-Löschung für Schüler)
# Sprint 8 Autoren: Mustafa Demiral, Ahmet Toplar (PBI 10.3 & 10.3.1: Buchlisten anlegen)
# Sprint 9 Autor: Mustafa Demiral (PBI 11.6 & 11.9: Bugfixes + Anti-Absturz-Logik)
# Sprint 10 Update:
# - PBI 11.5: Dynamische Schuljahre & Klassen in Dialogen (Synchron mit Schuljahrverwaltung)
# - PBI 11.3: Archiv-Ansicht für inaktive Schüler integriert
# Stand: Soft-Delete implementiert, Mac-DarkMode-Fix für Listen integriert, Buchlisten-Tab integriert.
#
# Refactoring-Hinweis:
# - Header, Breadcrumb, Seitentitel und Footer werden jetzt zentral
#   über BasePageWidget bereitgestellt.
# - Dadurch wird Code-Duplikation reduziert und das Layout ist
#   konsistent mit den anderen GUI-Ansichten.
# ------------------------------------------------------------------------------

import csv
from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout,
    QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QFileDialog, QMessageBox, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QBrush

from database_manager import DatabaseManager
from base_page import BasePageWidget

BUTTON_RADIUS = 10


def get_btn_style(bg_color, text_color="white"):
    return f"""
    QPushButton {{
        background-color: {bg_color};
        color: {text_color};
        padding: 8px 20px;
        border: 3px solid {bg_color};
        border-radius: {BUTTON_RADIUS}px;
        font-weight: bold;
        font-size: 14px;
    }}
    QPushButton:hover, QPushButton:focus {{
        border: 3px solid #000000;
    }}
    QPushButton:pressed {{
        background-color: #444444;
        border: 3px solid #000000;
        color: white;
    }}
    QPushButton:disabled {{
        background-color: #CFCFCF;
        border: 3px solid #CFCFCF;
        color: #888888;
    }}
    """


def get_import_btn_style():
    return f"""
    QPushButton {{
        background-color: #FFFFFF;
        color: #333333;
        padding: 8px 20px;
        border: 2px solid #D9DDE3;
        border-radius: {BUTTON_RADIUS}px;
        font-weight: bold;
        font-size: 14px;
    }}
    QPushButton:hover, QPushButton:focus {{
        border: 2px solid #000000;
        background-color: #F7F7F7;
    }}
    QPushButton:pressed {{
        background-color: #F0F0F0;
        border: 2px solid #000000;
        color: #333333;
    }}
    """


def get_input_style(accent_color="#F1BD4D"):
    return f"""
    QLineEdit, QComboBox {{
        padding: 12px;
        border: 1px solid #CCCCCC;
        border-radius: {BUTTON_RADIUS}px;
        background-color: #FFFFFF;
        color: #333333;
        font-size: 14px;
    }}
    QLineEdit:hover, QComboBox:hover {{
        border: 1px solid #999999;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {accent_color};
    }}
    """


def get_list_style():
    return f"""
    QListWidget {{
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: {BUTTON_RADIUS}px;
        padding: 5px;
        font-size: 14px;
    }}
    QListWidget::item {{
        padding: 8px;
        color: #333333;
    }}
    QListWidget::item:selected {{
        background-color: #F1BD4D;
        color: #FFFFFF;
        border-radius: 5px;
    }}
    QListWidget::item:hover:!selected {{
        background-color: #E0E0E0;
        color: #000000;
    }}
    """


class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None, warning_text="⚠️ Möchten Sie diesen Datensatz wirklich\nunwiderruflich löschen?"):
        super().__init__(parent)
        self.setWindowTitle("Löschen bestätigen")
        self.setFixedSize(450, 180)
        self.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(self)
        self.label = QLabel(warning_text)
        self.label.setFont(QFont("Open Sans", 11, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(self.label)
        btn_layout = QHBoxLayout()
        self.btn_no = QPushButton("Abbrechen")
        self.btn_yes = QPushButton("Löschen")
        self.btn_yes.setStyleSheet(get_btn_style("#D32F2F"))
        self.btn_no.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)


class StudentDeleteDialog(QDialog):
    def __init__(self, parent=None, student_name=""):
        super().__init__(parent)
        self.setWindowTitle("Schüler verwalten")
        self.setFixedSize(480, 260)
        self.setStyleSheet("background-color: #FFFFFF; color: #333333;")

        self.result_action = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        info_text = (f"Was möchten Sie mit dem Schüler '{student_name}' tun?\n\n"
                     "DEAKTIVIEREN: Schüler verschwindet aus der Liste, bleibt aber als Archiv im System.\n\n"
                     "LÖSCHEN: Schüler wird unwiderruflich gelöscht (Nur mit Admin-Passwort).")

        lbl = QLabel(info_text)
        lbl.setFont(QFont("Open Sans", 10))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Admin-Passwort (nur für endgültiges Löschen)")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setStyleSheet(get_input_style())
        layout.addWidget(self.pw_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_deactivate = QPushButton("Deaktivieren")
        self.btn_delete = QPushButton("Endgültig Löschen")

        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_deactivate.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_delete.setStyleSheet(get_btn_style("#D32F2F"))

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_deactivate.clicked.connect(self.do_deactivate)
        self.btn_delete.clicked.connect(self.do_delete)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_deactivate)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    def do_deactivate(self):
        self.result_action = 'deactivate'
        self.accept()

    def do_delete(self):
        if self.pw_input.text() == "admin123":
            self.result_action = 'delete'
            self.accept()
        else:
            self.error_label.setText("Falsches Admin-Passwort! Löschen verweigert.")


class CleanArchiveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Archiv leeren")
        self.setFixedSize(480, 220)
        self.setStyleSheet("background-color: #FFFFFF; color: #333333;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel(
            "Möchten Sie wirklich ALLE inaktiven Schüler endgültig aus dem System löschen?\nDieser Schritt kann nicht rückgängig gemacht werden.")
        lbl.setFont(QFont("Open Sans", 10, QFont.Weight.Bold))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Admin-Passwort eingeben")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setStyleSheet(get_input_style())
        layout.addWidget(self.pw_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_delete = QPushButton("Alle Inaktiven Löschen")

        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_delete.setStyleSheet(get_btn_style("#D32F2F"))

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_delete.clicked.connect(self.do_delete)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    def do_delete(self):
        if self.pw_input.text() == "admin123":
            self.accept()
        else:
            self.error_label.setText("Falsches Admin-Passwort!")


# --- PBI 11.3: Archiv-Dialog für inaktive Schüler mit Button-Fix ---
class InactiveStudentsDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Archiv - Inaktive Schüler")
        self.setFixedSize(900, 500)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)

        title = QLabel("Inaktive Schüler (Archiv)")
        title.setFont(QFont("Open Sans", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nachname", "Vorname", "Klasse", "Aktionen"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { gridline-color: #EEE; color: black; background-color: #FFFFFF; }")
        layout.addWidget(self.table)

        self.refresh_data()

        btn_close = QPushButton("Schließen")
        btn_close.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def refresh_data(self):
        self.table.setRowCount(0)
        if not self.db_manager: return

        conn = self.db_manager._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                               SELECT s.studierende_id, s.nachname, s.vorname, sk.name, sj.jahr
                               FROM Studierende s
                                        JOIN Schulklasse sk ON s.schulklasse_id = sk.schulklasse_id
                                        JOIN Schuljahr sj ON sk.schuljahr_id = sj.schuljahr_id
                               WHERE s.status = 'INAKTIV'
                               """)
                inactive = cursor.fetchall()
                self.table.setRowCount(len(inactive))

                # Kompakter Style für Tabellen-Buttons
                table_btn_style = """
                    QPushButton {
                        padding: 4px 8px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 12px;
                        min-width: 120px;
                        color: white;
                        border: none;
                    }
                """

                for row, s in enumerate(inactive):
                    display_id = s[0] % 10000
                    safe_jahr = str(s[4]).replace('/', '-')
                    formatted_id = f"{s[3]}_{safe_jahr}_{display_id:03d}"

                    self.table.setItem(row, 0, QTableWidgetItem(formatted_id))
                    self.table.setItem(row, 1, QTableWidgetItem(str(s[1])))
                    self.table.setItem(row, 2, QTableWidgetItem(str(s[2])))
                    self.table.setItem(row, 3, QTableWidgetItem(str(s[3])))

                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(10, 2, 10, 2)
                    action_layout.setSpacing(15)
                    action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    btn_reactivate = QPushButton("Aktiv setzen")
                    btn_reactivate.setStyleSheet(
                        table_btn_style + "QPushButton { background-color: #4CAF50; } QPushButton:hover { background-color: #45a049; }")
                    btn_reactivate.clicked.connect(lambda ch, sid=s[0]: self.reactivate(sid))

                    btn_delete = QPushButton("Endgültig Löschen")
                    btn_delete.setStyleSheet(
                        table_btn_style + "QPushButton { background-color: #D32F2F; } QPushButton:hover { background-color: #b71c1c; }")
                    btn_delete.clicked.connect(lambda ch, sid=s[0]: self.final_delete(sid))

                    action_layout.addWidget(btn_reactivate)
                    action_layout.addWidget(btn_delete)
                    self.table.setCellWidget(row, 4, action_widget)
        finally:
            conn.close()

    def reactivate(self, sid):
        conn = self.db_manager._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Studierende SET status = 'AKTIV' WHERE studierende_id = %s", (sid,))
            conn.commit()
            self.refresh_data()
        finally:
            conn.close()

    def final_delete(self, sid):
        confirm = DeleteConfirmDialog(self, "Diesen Schüler wirklich permanent löschen?")
        if confirm.exec() == QDialog.DialogCode.Accepted:
            self.db_manager.delete_student(sid)
            self.refresh_data()


# ==============================================================================
# DIALOGE
# ==============================================================================

class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neuer Schüler" if not student_data else "Schüler bearbeiten")
        self.setFixedSize(400, 380)
        self.setStyleSheet(f"""
        QDialog {{ background-color: #FFFFFF; }}
        QLabel {{ color: #333333; font-weight: bold; }}
        QLineEdit, QComboBox {{
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: {BUTTON_RADIUS}px;
            padding: 8px;
            color: #333333;
            font-size: 14px;
        }}
        QLineEdit:hover, QComboBox:hover {{ border: 1px solid #999999; }}
        QLineEdit:focus, QComboBox:focus {{ border: 2px solid #F1BD4D; }}
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname eingeben")
        self.input_nachname = QLineEdit()
        self.input_nachname.setPlaceholderText("Nachname eingeben")

        # PBI 11.5: Dynamisches Laden aus DB
        self.combo_klasse = QComboBox()
        self.combo_klasse.addItem("Bitte wählen...")
        self.combo_jahr = QComboBox()
        self.combo_jahr.addItem("Bitte wählen...")

        if parent and hasattr(parent, 'db_manager'):
            klassen = parent.db_manager.get_classes()
            klassen_namen = sorted(list(set(k[1] for k in klassen)))
            self.combo_klasse.addItems(klassen_namen)
            jahre = parent.db_manager.get_school_years()
            self.combo_jahr.addItems([str(j[1]) for j in jahre])

        self.id_prefix_label = QLabel("..._..._")
        self.id_prefix_label.setStyleSheet("color: #666666; font-style: italic; font-weight: normal;")

        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("Auto")
        self.input_id.setFixedWidth(80)

        id_layout = QHBoxLayout()
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.addWidget(self.id_prefix_label)
        id_layout.addWidget(self.input_id)
        id_layout.addStretch()

        for w in [self.input_vorname, self.input_nachname, self.combo_klasse, self.combo_jahr]:
            w.setFixedWidth(250)

        self.error_label = QLabel("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
        self.error_label.setStyleSheet("color: #D32F2F; font-size: 12px; font-style: italic;")
        self.error_label.hide()

        self.combo_klasse.currentTextChanged.connect(self.update_id_prefix)
        self.combo_jahr.currentTextChanged.connect(self.update_id_prefix)

        if student_data:
            display_id = int(student_data[0]) % 10000
            self.input_id.setText(f"{display_id:03d}")
            self.input_nachname.setText(str(student_data[1]))
            self.input_vorname.setText(str(student_data[2]))
            self.combo_klasse.setCurrentText(str(student_data[3]))
            if len(student_data) > 4:
                self.combo_jahr.setCurrentText(str(student_data[4]))
            self.update_id_prefix()

        form_layout.addRow(QLabel("Vorname*:"), self.input_vorname)
        form_layout.addRow(QLabel("Nachname*:"), self.input_nachname)
        form_layout.addRow(QLabel("Klasse*:"), self.combo_klasse)
        form_layout.addRow(QLabel("Schuljahr*:"), self.combo_jahr)
        form_layout.addRow(QLabel("ID-Nummer:"), id_layout)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def update_id_prefix(self):
        klasse = self.combo_klasse.currentText()
        jahr = self.combo_jahr.currentText()
        if klasse != "Bitte wählen..." and jahr != "Bitte wählen...":
            safe_jahr = jahr.replace('/', '-')
            self.id_prefix_label.setText(f"{klasse}_{safe_jahr}_")
        else:
            self.id_prefix_label.setText("..._..._")

    def validate_and_save(self):
        valid = True

        def check_field(widget, is_invalid):
            if is_invalid:
                widget.setStyleSheet(f"border: 2px solid #D32F2F; border-radius: {BUTTON_RADIUS}px;")
                return False
            widget.setStyleSheet("")
            return True

        valid &= check_field(self.input_vorname, not self.input_vorname.text().strip())
        valid &= check_field(self.input_nachname, not self.input_nachname.text().strip())
        valid &= check_field(self.combo_klasse, self.combo_klasse.currentText() == "Bitte wählen...")
        valid &= check_field(self.combo_jahr, self.combo_jahr.currentText() == "Bitte wählen...")

        manual_id = self.input_id.text().strip()
        is_id_invalid = bool(manual_id) and not manual_id.isdigit()
        valid &= check_field(self.input_id, is_id_invalid)

        if not valid:
            if is_id_invalid:
                self.error_label.setText("Die ID-Nummer darf nur aus Zahlen bestehen!")
            else:
                self.error_label.setText("Bitte alle markierten Pflichtfelder (*) ausfüllen.")
            self.error_label.show()
        else:
            self.accept()


class KlassenDialog(QDialog):
    def __init__(self, parent=None, klassen_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Klasse" if not klassen_data else "Klasse bearbeiten")
        self.setFixedSize(400, 260)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #FFFFFF; }}
            QLabel {{ color: #333333; font-weight: bold; }}
            QLineEdit, QComboBox {{
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: {BUTTON_RADIUS}px;
                padding: 8px;
                color: #333333;
                font-size: 14px;
            }}
            QLineEdit:hover, QComboBox:hover {{ border: 1px solid #999999; }}
            QLineEdit:focus, QComboBox:focus {{ border: 2px solid #F1BD4D; }}
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. MB")
        self.combo_jahr = QComboBox()
        self.combo_jahr.addItem("Bitte wählen...")

        if parent and hasattr(parent, 'db_manager'):
            jahre = parent.db_manager.get_school_years()
            self.combo_jahr.addItems([str(j[1]) for j in jahre])

        for w in [self.input_name, self.combo_jahr]:
            w.setFixedWidth(250)

        if klassen_data:
            self.input_name.setText(klassen_data[1])
            self.combo_jahr.setCurrentText(klassen_data[2])

        form_layout.addRow(QLabel("Klassenname:"), self.input_name)
        form_layout.addRow(QLabel("Schuljahr:"), self.combo_jahr)
        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)


class SchuljahrDialog(QDialog):
    def __init__(self, parent=None, jahr_data=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Schuljahr" if not jahr_data else "Schuljahr bearbeiten")
        self.setFixedSize(400, 220)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #FFFFFF; }}
            QLabel {{ color: #333333; font-weight: bold; }}
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: {BUTTON_RADIUS}px;
                padding: 8px;
                color: #333333;
                font-size: 14px;
            }}
            QLineEdit:hover {{ border: 1px solid #999999; }}
            QLineEdit:focus {{ border: 2px solid #F1BD4D; }}
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. 2025-26")
        self.input_name.setFixedWidth(250)

        if jahr_data:
            self.input_name.setText(jahr_data[1])

        form_layout.addRow(QLabel("Schuljahr:"), self.input_name)
        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_save = QPushButton("Speichern")
        self.btn_cancel.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_save.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)


# ==============================================================================
# TABS
# ==============================================================================

class BaseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 20, 15, 10)
        self.main_layout.setSpacing(15)
        self.input_style = get_input_style("#F1BD4D")

    def setup_table(self, col_count, headers):
        self.table = QTableWidget(0, col_count)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F9F9F9;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                gridline-color: #EDEDED;
                color: #000000;
                font-size: 14px;
            }
        """)

        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F0F0F0;
                color: #333333;
                font-weight: bold;
                border: none;
                border-bottom: 3px solid #F1BD4D;
                padding: 12px;
            }
        """)

        self.main_layout.addWidget(self.table)

    def show_popup(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(f"""
            QLabel {{
                color: #000000;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: #E0E0E0;
                color: #333333;
                padding: 8px 16px;
                border-radius: {BUTTON_RADIUS}px;
                border: 1px solid #CCCCCC;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #D0D0D0;
                border: 1px solid #333333;
            }}
        """)
        msg.exec()


class SchuelerTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Name, Klasse oder Jahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Klassen (Alle)")
        self.filter_combo.setFixedWidth(180)
        self.filter_combo.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItem("Schuljahre (Alle)")
        self.filter_jahr.setFixedWidth(180)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_combo)
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        self.setup_table(6, ["ID", "Nachname", "Vorname", "Klasse", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schüler hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_student_dialog)

        btn_import = QPushButton("📥 Schüler importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_students)

        # NEUER BUTTON: Archiv
        btn_archive = QPushButton("📁 Inaktive Schüler (Archiv)")
        btn_archive.setStyleSheet(get_import_btn_style())
        btn_archive.clicked.connect(self.open_archive_dialog)

        btn_clean = QPushButton("🗑️ Archiv leeren")
        btn_clean.setStyleSheet(get_import_btn_style())
        btn_clean.clicked.connect(self.clean_archive)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        footer_layout.addWidget(btn_archive)
        footer_layout.addWidget(btn_clean)
        self.main_layout.addLayout(footer_layout)

        self.search_input.textChanged.connect(self.refresh_data)
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        self.filter_jahr.currentTextChanged.connect(self.refresh_data)

        if self.db_manager:
            self.refresh_filter_lists()
            self.refresh_data()

    def refresh_filter_lists(self):
        """PBI 11.5: Synchronisiert Filter mit DB."""
        if not self.db_manager: return
        self.filter_combo.blockSignals(True)
        self.filter_jahr.blockSignals(True)

        curr_kl = self.filter_combo.currentText()
        curr_jr = self.filter_jahr.currentText()

        self.filter_combo.clear()
        self.filter_combo.addItem("Klassen (Alle)")
        klassen = self.db_manager.get_classes()
        namen = sorted(list(set(k[1] for k in klassen)))
        self.filter_combo.addItems(namen)

        self.filter_jahr.clear()
        self.filter_jahr.addItem("Schuljahre (Alle)")
        jahre = self.db_manager.get_school_years()
        self.filter_jahr.addItems([str(j[1]) for j in jahre])

        self.filter_combo.setCurrentText(curr_kl if self.filter_combo.findText(curr_kl) != -1 else "Klassen (Alle)")
        self.filter_jahr.setCurrentText(curr_jr if self.filter_jahr.findText(curr_jr) != -1 else "Schuljahre (Alle)")

        self.filter_combo.blockSignals(False)
        self.filter_jahr.blockSignals(False)

    def refresh_data(self):
        if not self.db_manager:
            return

        try:
            search_text = self.search_input.text().lower()
            all_matching_students = self.db_manager.get_students()

            selected_klasse = self.filter_combo.currentText()
            selected_jahr = self.filter_jahr.currentText()

            filtered_students = []
            for s in all_matching_students:
                formatted_id = str(s[5])
                nachname = str(s[1]).lower()
                vorname = str(s[2]).lower()

                match_text = search_text in formatted_id.lower() or search_text in nachname or search_text in vorname
                match_klasse = (selected_klasse == "Klassen (Alle)" or s[3] == selected_klasse)
                match_jahr = (selected_jahr == "Schuljahre (Alle)" or s[4] == selected_jahr)

                if match_text and match_klasse and match_jahr:
                    filtered_students.append(s)

            self.load_table_data(filtered_students)
        except Exception as e:
            print(f"Fehler beim Laden der Schüler-Tabelle: {e}")

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))

        btn_edit_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 16px;
                color: #333333;
                border-radius: {BUTTON_RADIUS}px;
            }}
            QPushButton:hover {{
                background-color: #E0E0E0;
            }}
        """
        btn_delete_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 16px;
                color: #333333;
                border-radius: {BUTTON_RADIUS}px;
            }}
            QPushButton:hover {{
                background-color: #FFCDD2;
            }}
        """

        for row, student in enumerate(data_list):
            db_id = str(student[0])
            nachname = str(student[1])
            vorname = str(student[2])
            klasse = str(student[3])
            jahr = str(student[4])
            formatted_id = str(student[5])

            display_data = [formatted_id, nachname, vorname, klasse, jahr]
            full_name = f"{vorname} {nachname}"

            for col in range(5):
                item = QTableWidgetItem(display_data[col])
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QBrush(Qt.GlobalColor.black))
                if col in [0, 3, 4]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, sid=db_id: self.edit_student(sid))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, sid=db_id, sname=full_name: self.delete_student(sid, sname))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    def open_student_dialog(self):
        d = StudentDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            vorname = d.input_vorname.text().strip()
            nachname = d.input_nachname.text().strip()
            klasse = d.combo_klasse.currentText()
            jahr = d.combo_jahr.currentText()
            manual_id = d.input_id.text().strip()

            if self.db_manager:
                success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                if success:
                    self.refresh_data()
                    self.show_popup("Erfolg", f"Schüler {vorname} {nachname} wurde angelegt.")
                else:
                    self.show_popup("Fehler", f"Die ID {manual_id} ist in dieser Klasse bereits vergeben!")

    def edit_student(self, sid):
        if not self.db_manager:
            return
        current_data = self.db_manager.get_student_by_id(sid)
        if current_data:
            d = StudentDialog(self, student_data=current_data)
            if d.exec() == QDialog.DialogCode.Accepted:
                nachname = d.input_nachname.text().strip()
                vorname = d.input_vorname.text().strip()
                klasse = d.combo_klasse.currentText()
                jahr = d.combo_jahr.currentText()
                manual_id = d.input_id.text().strip()

                success = self.db_manager.update_student(int(sid), nachname, vorname, klasse, jahr, manual_id)
                if success:
                    self.refresh_data()
                else:
                    self.show_popup("Fehler", f"Die ID {manual_id} ist in dieser Klasse bereits vergeben!")

    def delete_student(self, sid, student_name):
        if not self.db_manager:
            return
        dialog = StudentDeleteDialog(self, student_name=student_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.result_action == 'deactivate':
                self.db_manager.deactivate_student(sid)
                self.refresh_data()
                self.show_popup("Erfolg", f"Der Schüler '{student_name}' wurde sicher inaktiv gesetzt.")
            elif dialog.result_action == 'delete':
                self.db_manager.delete_student(sid)
                self.refresh_data()
                self.show_popup("Erfolg", f"Der Schüler '{student_name}' wurde endgültig gelöscht.")

    # PBI 11.3: Archiv-Dialog aufrufen
    def open_archive_dialog(self):
        d = InactiveStudentsDialog(self, self.db_manager)
        d.exec()
        self.refresh_data()

    def clean_archive(self):
        if not self.db_manager:
            return
        dialog = CleanArchiveDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            deleted_count = self.db_manager.delete_all_inactive_students()
            self.refresh_data()
            self.show_popup(
                "Archiv geleert",
                f"Erfolgreich ausgeführt!\n\nEs wurden {deleted_count} inaktive Schüler dauerhaft aus der Datenbank gelöscht."
            )

    def import_students(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Schüler importieren", "",
            "Dateien (*.csv *.xlsx);;Alle Dateien (*.*)"
        )
        if not file_path:
            return

        if not self.db_manager:
            self.show_popup("Fehler", "Keine Datenbankverbindung!")
            return

        try:
            imported_count = 0
            skipped_count = 0

            if file_path.lower().endswith('.csv'):
                with open(file_path, mode='r', encoding='utf-8-sig') as file:
                    header_line = file.readline()
                    delim = ';' if ';' in header_line else ','
                    file.seek(0)
                    reader = csv.reader(file, delimiter=delim)
                    headers = next(reader, [])
                    id_idx, vn_idx, nn_idx, kl_idx, j_idx = -1, -1, -1, -1, -1
                    for i, h in enumerate(headers):
                        h_up = str(h).upper()
                        if "ID" in h_up and id_idx == -1:
                            id_idx = i
                        elif "VORNAME" in h_up:
                            vn_idx = i
                        elif "NACHNAME" in h_up:
                            nn_idx = i
                        elif "KLASSE" in h_up:
                            kl_idx = i
                        elif "JAHR" in h_up:
                            j_idx = i

                    if vn_idx == -1 or nn_idx == -1:
                        id_idx, vn_idx, nn_idx, kl_idx, j_idx = 0, 1, 2, 3, 4

                    for row in reader:
                        if len(row) > max(vn_idx, nn_idx):
                            raw_id = str(row[id_idx]).strip() if id_idx != -1 and id_idx < len(row) else ""
                            vorname = str(row[vn_idx]).strip()
                            nachname = str(row[nn_idx]).strip()
                            klasse = str(row[kl_idx]).strip()
                            jahr = str(row[j_idx]).strip()

                            if not vorname or not nachname: continue

                            manual_id = None
                            if raw_id:
                                try:
                                    if '_' in raw_id:
                                        manual_id = int(raw_id.split('_')[-1])
                                    else:
                                        manual_id = int(raw_id)
                                except ValueError:
                                    pass

                            try:
                                success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                                if success:
                                    imported_count += 1
                                else:
                                    skipped_count += 1
                            except:
                                skipped_count += 1

            elif file_path.lower().endswith('.xlsx'):
                try:
                    import pandas as pd
                except ImportError:
                    self.show_popup("Fehler", "Für den Excel-Import muss 'pandas' installiert sein!")
                    return
                df = pd.read_excel(file_path)
                id_col = None
                for col in df.columns:
                    if "ID" in str(col).strip().upper():
                        id_col = col
                        break

                for index, row in df.iterrows():
                    try:
                        raw_id = ""
                        if id_col and pd.notna(row.get(id_col)):
                            raw_id = str(row.get(id_col)).strip()

                        vorname = str(row.get('Vorname', '')).strip()
                        nachname = str(row.get('Nachname', '')).strip()
                        klasse = str(row.get('Klasse', '')).strip()
                        jahr = str(row.get('Eintrittsschuljahr', '')).strip()
                        if not jahr or jahr == 'nan':
                            jahr = str(row.get('Schuljahr', '')).strip()

                        if nachname and vorname and nachname != 'nan':
                            manual_id = None
                            if raw_id and raw_id.lower() != 'nan':
                                try:
                                    if '_' in raw_id:
                                        manual_id = int(raw_id.split('_')[-1])
                                    else:
                                        manual_id = int(float(raw_id))
                                except:
                                    pass

                            success = self.db_manager.add_student(nachname, vorname, klasse, jahr, manual_id)
                            if success:
                                imported_count += 1
                            else:
                                skipped_count += 1
                    except:
                        skipped_count += 1

            self.refresh_data()
            self.show_popup("Import abgeschlossen", f"Erfolgreich: {imported_count}\nÜbersprungen: {skipped_count}")

        except Exception as e:
            self.show_popup("Achtung", f"Der Import wurde abgebrochen:\n\n{e}")


class KlassenTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Klasse...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)

        self.filter_jahr = QComboBox()
        self.filter_jahr.addItem("Schuljahre (Alle)")
        self.refresh_year_filter()
        self.filter_jahr.setFixedWidth(200)
        self.filter_jahr.setStyleSheet(self.input_style)

        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        action_layout.addWidget(self.filter_jahr)
        self.main_layout.addLayout(action_layout)

        self.setup_table(4, ["Schuljahr", "Klasse", "Anzahl Schüler", "Aktionen"])
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)

        self.search_input.textChanged.connect(self.filter_table)
        self.filter_jahr.currentTextChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Klasse hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_klassen_dialog)

        btn_import = QPushButton("📥 Klassen importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_klassen)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        self.main_layout.addLayout(footer_layout)

        self.filter_table()

    def refresh_year_filter(self):
        if not self.db_manager: return

        try:
            current_text = self.filter_jahr.currentText()
            self.filter_jahr.blockSignals(True)
            self.filter_jahr.clear()
            self.filter_jahr.addItem("Schuljahre (Alle)")
            jahre = self.db_manager.get_school_years()
            for j in jahre:
                self.filter_jahr.addItem(str(j[1]))
            index = self.filter_jahr.findText(current_text)
            if index >= 0:
                self.filter_jahr.setCurrentIndex(index)
            self.filter_jahr.blockSignals(False)
        except Exception as e:
            print(f"Fehler beim Laden des Klassen-Filters: {e}")

    def filter_table(self):
        if not self.db_manager: return

        try:
            alle_klassen_roh = self.db_manager.get_classes()
            alle_aktiven_schueler = self.db_manager.get_students()

            echte_counts = {}
            for s in alle_aktiven_schueler:
                key = (str(s[3]), str(s[4]))
                echte_counts[key] = echte_counts.get(key, 0) + 1

            txt = self.search_input.text().lower()
            jahr_filter = self.filter_jahr.currentText()

            gefiltert = []
            for k in alle_klassen_roh:
                s_jahr, s_name = str(k[0]), str(k[1])

                echte_anzahl = echte_counts.get((s_name, s_jahr), 0)
                korrigierte_klasse = (s_jahr, s_name, echte_anzahl)

                match_txt = txt in s_name.lower() or txt in s_jahr.lower()
                match_jahr = (jahr_filter == "Schuljahre (Alle)" or jahr_filter == s_jahr)

                if match_txt and match_jahr:
                    gefiltert.append(korrigierte_klasse)

            self.load_table_data(gefiltert)
        except Exception as e:
            print(f"Fehler im KlassenTab: {e}")

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_edit_style = f"QPushButton {{ background: transparent; border: none; font-size: 16px; color: #333333; border-radius: {BUTTON_RADIUS}px; }} QPushButton:hover {{ background-color: #E0E0E0; }}"
        btn_delete_style = f"QPushButton {{ background: transparent; border: none; font-size: 16px; color: #333333; border-radius: {BUTTON_RADIUS}px; }} QPushButton:hover {{ background-color: #FFCDD2; }}"

        for row, klasse in enumerate(data_list):
            self.table.setItem(row, 0, self._create_readonly_item(str(klasse[0])))
            self.table.setItem(row, 1, self._create_readonly_item(str(klasse[1])))
            self.table.setItem(row, 2, self._create_readonly_item(str(klasse[2])))

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            kid = f"{klasse[1]}_{klasse[0]}"
            kname = f"{klasse[1]} ({klasse[0]})"

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setStyleSheet(btn_edit_style)
            btn_edit.clicked.connect(lambda ch, id=kid: self.edit_klasse(id))

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(30, 30)
            btn_delete.setStyleSheet(btn_delete_style)
            btn_delete.clicked.connect(lambda ch, id=kid, name=kname: self.delete_klasse(id, name))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 3, action_widget)

    def _create_readonly_item(self, text):
        """Hilfsmethode für einheitliche Items"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        item.setForeground(QBrush(Qt.GlobalColor.black))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def open_klassen_dialog(self):
        d = KlassenDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            sj = d.combo_jahr.currentText()
            if name and sj != "Bitte wählen...":
                if self.db_manager.add_class(name, sj):
                    self.filter_table()
                else:
                    self.show_popup("Fehler", "Klasse konnte nicht gespeichert werden.")

    def edit_klasse(self, kid):
        self.show_popup("Info", f"Bearbeiten-Funktion für {kid} folgt in Kürze.")

    def delete_klasse(self, kid, klasse_name):
        dialog = StudentDeleteDialog(self, klasse_name)
        dialog.setWindowTitle("Klasse verwalten")

        if hasattr(dialog, 'label'):
            dialog.label.setText(f"Was möchten Sie mit der Klasse '{klasse_name}' tun?")

        for label in dialog.findChildren(QLabel):
            if "Schüler" in label.text():
                label.setText(label.text().replace("Schüler", "Klasse"))

        if hasattr(dialog, 'btn_deactivate'):
            dialog.btn_deactivate.show()

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            if dialog.pw_input.text() == "admin123":
                try:
                    parts = kid.split('_')
                    if len(parts) >= 2:
                        k_name, k_jahr = parts[0], parts[1]
                        self.db_manager.delete_class(k_name, k_jahr)
                        self.filter_table()
                except Exception as e:
                    print(f"Fehler beim Löschen der Klasse: {e}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Abgelehnt", "Falsches Admin-Passwort!")

    def import_klassen(self):
        self.show_popup("Info", "Import-Schnittstelle wird für MariaDB optimiert.")


class SchuljahrTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        action_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suche nach Schuljahr...")
        self.search_input.setFixedWidth(400)
        self.search_input.setStyleSheet(self.input_style)
        action_layout.addWidget(self.search_input)
        action_layout.addStretch()
        self.main_layout.addLayout(action_layout)

        self.setup_table(3, ["ID", "Schuljahr", "Aktionen"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)

        self.search_input.textChanged.connect(self.filter_table)

        footer_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Schuljahr hinzufügen")
        btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        btn_add.clicked.connect(self.open_jahr_dialog)

        btn_import = QPushButton("📥 Schuljahre importieren")
        btn_import.setStyleSheet(get_import_btn_style())
        btn_import.clicked.connect(self.import_jahre)

        footer_layout.addWidget(btn_add)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_import)
        self.main_layout.addLayout(footer_layout)

        self.filter_table()

    def filter_table(self):
        if not self.db_manager: return

        try:
            txt = self.search_input.text().lower()
            alle_jahre = self.db_manager.get_school_years()
            gefiltert = [j for j in alle_jahre if txt in str(j[1]).lower()]
            self.load_table_data(gefiltert)
        except Exception as e:
            print(f"Fehler beim Laden der Schuljahre: {e}")

    def load_table_data(self, data_list):
        self.table.setRowCount(len(data_list))
        btn_style = f"""
            QPushButton {{ background: transparent; border: none; font-size: 16px; color: #333333; border-radius: {BUTTON_RADIUS}px; }}
            QPushButton:hover {{ background-color: #FFCDD2; }}
        """

        for row, jahr_row in enumerate(data_list):
            for col in range(2):
                item = QTableWidgetItem(str(jahr_row[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QBrush(Qt.GlobalColor.black))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet(btn_style)
            btn_delete.clicked.connect(lambda ch, jid=jahr_row[0], jname=str(jahr_row[1]): self.delete_jahr(jid, jname))

            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 2, action_widget)

    def open_jahr_dialog(self):
        d = SchuljahrDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            name = d.input_name.text().strip()
            if name and self.db_manager:
                self.db_manager.add_school_year(name)
                self.filter_table()

    def delete_jahr(self, jid, jahr_name):
        dialog = StudentDeleteDialog(self, jahr_name)

        if hasattr(dialog, 'btn_deactivate'):
            dialog.btn_deactivate.hide()

        if hasattr(dialog, 'label'):
            dialog.label.setText(f"Möchten Sie das Schuljahr '{jahr_name}' wirklich löschen?\n\n"
                                 f"UNG: Dadurch werden auch alle zugeordeten Klassen und "
                                 f"Schüler unwiderruflich entfernt!")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.pw_input.text() == "admin123":
                try:
                    self.db_manager.delete_school_year(jid)
                    self.filter_table()
                    if hasattr(self, 'show_popup'):
                        self.show_popup("Erfolg", f"Schuljahr {jahr_name} wurde gelöscht.")
                except Exception as e:
                    print(f"Fehler: {e}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Abgelehnt", "Falsches Admin-Passwort!")

    def import_jahre(self):
        self.show_popup("Info", "Import-Funktion wird vorbereitet.")


class BuchlistenTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = parent.db_manager if parent else None

        top_layout = QHBoxLayout()
        lbl_klasse = QLabel("Buchliste bearbeiten für Klasse:")
        lbl_klasse.setStyleSheet("color: #333333; font-weight: bold; font-size: 14px;")
        top_layout.addWidget(lbl_klasse)

        self.combo_klasse = QComboBox()
        self.combo_klasse.setStyleSheet(self.input_style)
        self.combo_klasse.setFixedWidth(250)
        self.combo_klasse.currentTextChanged.connect(self.load_current_list)
        top_layout.addWidget(self.combo_klasse)
        top_layout.addStretch()
        self.main_layout.addLayout(top_layout)

        dual_list_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        lbl_left = QLabel("Verfügbare Bücher (Alphabetisch):")
        lbl_left.setStyleSheet("color: #333333; font-weight: bold; font-size: 14px;")
        left_layout.addWidget(lbl_left)

        self.list_all_books = QListWidget()
        self.list_all_books.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_all_books.setStyleSheet(get_list_style())
        self.list_all_books.itemDoubleClicked.connect(self.add_book)
        left_layout.addWidget(self.list_all_books)

        btn_layout = QVBoxLayout()
        btn_layout.addStretch()

        self.btn_add = QPushButton("➔")
        self.btn_add.setStyleSheet(get_btn_style("#F1BD4D"))
        self.btn_add.setToolTip("Zur Klassenliste hinzufügen")
        self.btn_add.clicked.connect(self.add_book)

        self.btn_remove = QPushButton("←")
        self.btn_remove.setStyleSheet(get_btn_style("#E0E0E0", "#333333"))
        self.btn_remove.setToolTip("Aus Klassenliste entfernen")
        self.btn_remove.clicked.connect(self.remove_book)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch()

        right_layout = QVBoxLayout()
        lbl_right = QLabel("Benötigte Bücher der Klasse:")
        lbl_right.setStyleSheet("color: #333333; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(lbl_right)

        self.list_class_books = QListWidget()
        self.list_class_books.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_class_books.setStyleSheet(get_list_style())
        self.list_class_books.itemDoubleClicked.connect(self.remove_book)
        right_layout.addWidget(self.list_class_books)

        dual_list_layout.addLayout(left_layout, 2)
        dual_list_layout.addLayout(btn_layout, 1)
        dual_list_layout.addLayout(right_layout, 2)
        self.main_layout.addLayout(dual_list_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_save = QPushButton("💾 Buchliste speichern")
        self.btn_save.setStyleSheet(get_btn_style("#5CB1D6"))
        self.btn_save.clicked.connect(self.save_list)
        bottom_layout.addWidget(self.btn_save)
        self.main_layout.addLayout(bottom_layout)

        self.all_books_cache = {}
        self.refresh_dropdown_and_books()

    def refresh_dropdown_and_books(self):
        if not self.db_manager: return

        try:
            self.combo_klasse.blockSignals(True)
            self.combo_klasse.clear()
            klassen = self.db_manager.get_classes()
            for k in klassen:
                self.combo_klasse.addItem(f"{k[1]} ({k[0]})", userData={"name": k[1], "jahr": k[0]})
            self.combo_klasse.blockSignals(False)

            buecher = self.db_manager.get_books("", "Titel")
            self.all_books_cache.clear()
            for b in buecher:
                isbn = str(b[0])
                titel = str(b[1])
                self.all_books_cache[isbn] = f"{titel} (ISBN: {isbn})"
            self.load_current_list()
        except Exception as e:
            print(f"Fehler beim Laden der Buchlisten: {e}")

    def load_current_list(self):
        try:
            self.list_all_books.clear()
            self.list_class_books.clear()
            if self.combo_klasse.currentIndex() == -1: return
            klasse_data = self.combo_klasse.currentData()
            if not klasse_data: return

            selected_isbns = self.db_manager.get_class_booklist(klasse_data["name"], klasse_data["jahr"])
            sorted_books = sorted(self.all_books_cache.items(), key=lambda x: x[1])

            for isbn, text in sorted_books:
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, isbn)
                if isbn in selected_isbns:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    item.setForeground(QBrush(Qt.GlobalColor.gray))
                    right_item = QListWidgetItem(text)
                    right_item.setData(Qt.ItemDataRole.UserRole, isbn)
                    self.list_class_books.addItem(right_item)
                self.list_all_books.addItem(item)
        except Exception as e:
            print(f"Fehler bei der aktuellen Klassenliste: {e}")

    def add_book(self):
        for item in self.list_all_books.selectedItems():
            if not item.flags() & Qt.ItemFlag.ItemIsEnabled: continue
            isbn = item.data(Qt.ItemDataRole.UserRole)
            right_item = QListWidgetItem(item.text())
            right_item.setData(Qt.ItemDataRole.UserRole, isbn)
            self.list_class_books.addItem(right_item)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            item.setForeground(QBrush(Qt.GlobalColor.gray))
            item.setSelected(False)

    def remove_book(self):
        for right_item in self.list_class_books.selectedItems():
            isbn = right_item.data(Qt.ItemDataRole.UserRole)
            row = self.list_class_books.row(right_item)
            self.list_class_books.takeItem(row)
            for i in range(self.list_all_books.count()):
                left_item = self.list_all_books.item(i)
                if left_item.data(Qt.ItemDataRole.UserRole) == isbn:
                    left_item.setFlags(left_item.flags() | Qt.ItemFlag.ItemIsEnabled)
                    left_item.setForeground(QBrush(Qt.GlobalColor.black))
                    break

    def save_list(self):
        if self.combo_klasse.currentIndex() == -1: return
        klasse_data = self.combo_klasse.currentData()
        isbns_to_save = []
        for i in range(self.list_class_books.count()):
            item = self.list_class_books.item(i)
            isbns_to_save.append(item.data(Qt.ItemDataRole.UserRole))
        success = self.db_manager.save_class_booklist(klasse_data["name"], klasse_data["jahr"], isbns_to_save)
        if success:
            self.show_popup("Erfolg", f"Buchliste für {klasse_data['name']} erfolgreich gespeichert!")
        else:
            self.show_popup("Fehler", "Beim Speichern ist ein Fehler aufgetreten.")


# ==============================================================================
# CONTAINER
# ==============================================================================
class SchuelerverwaltungWidget(BasePageWidget):
    """
    Container-Widget für Schüler-, Klassen-, Schuljahr- und Buchlistenverwaltung.
    """
    COLOR = "#F1BD4D"

    def __init__(self, parent=None):
        super().__init__(
            breadcrumb_text="Startseite > Hauptmenü > Schülerverwaltung > Schüler",
            page_title="Schülerverwaltung",
            accent_color=self.COLOR,
            parent=parent
        )

        self.db_manager = parent.db_manager if parent else None

        self.tabs = QTabWidget()
        self.tabs.tabBar().setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #CCCCCC;
                border-radius: 12px;
                background-color: #FFFFFF;
            }}
            QTabBar::tab {{
                background-color: #F0F0F0;
                color: #333333;
                padding: 12px 0px;
                font-weight: bold;
                font-size: 15px;
                border: 1px solid #CCCCCC;
                border-bottom: none;
                border-top-left-radius: {BUTTON_RADIUS}px;
                border-top-right-radius: {BUTTON_RADIUS}px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: #F1BD4D;
                color: #FFFFFF;
                border-color: #F1BD4D;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #E0E0E0;
            }}
        """)

        self.tab_schueler = SchuelerTab(self)
        self.tab_klassen = KlassenTab(self)
        self.tab_schuljahr = SchuljahrTab(self)
        self.tab_buchlisten = BuchlistenTab(self)

        self.tabs.addTab(self.tab_schueler, "👨‍🎓 Schüler")
        self.tabs.addTab(self.tab_klassen, "🏫 Klassen")
        self.tabs.addTab(self.tab_schuljahr, "📅 Schuljahre")
        self.tabs.addTab(self.tab_buchlisten, "📚 Buchlisten")

        self.tabs.currentChanged.connect(self.update_header_text)
        self.content_layout.addWidget(self.tabs)

    def update_header_text(self, index):
        # ----------------------------------------------------------------------
        # BUGFIX: Try-Except (Airbag) um den Tab-Wechsel!
        # Falls z.B. set_breadcrumb noch von der alten BasePage fehlt oder
        # die Datenbank kurz abbricht, crasht PyQt6 so nicht mehr.
        # ----------------------------------------------------------------------
        try:
            if index == 0:
                if hasattr(self, 'set_breadcrumb'): self.set_breadcrumb(
                    "Startseite > Hauptmenü > Schülerverwaltung > Schüler")
                if hasattr(self, 'set_page_title'): self.set_page_title("Schülerverwaltung")
                self.tab_schueler.refresh_filter_lists()
                self.tab_schueler.refresh_data()
            elif index == 1:
                if hasattr(self, 'set_breadcrumb'): self.set_breadcrumb(
                    "Startseite > Hauptmenü > Schülerverwaltung > Schulklassen")
                if hasattr(self, 'set_page_title'): self.set_page_title("Schulklassenverwaltung")
                self.tab_klassen.refresh_year_filter()
                self.tab_klassen.filter_table()
            elif index == 2:
                if hasattr(self, 'set_breadcrumb'): self.set_breadcrumb(
                    "Startseite > Hauptmenü > Schülerverwaltung > Schuljahre")
                if hasattr(self, 'set_page_title'): self.set_page_title("Schuljahrverwaltung")
                self.tab_schuljahr.filter_table()
            elif index == 3:
                if hasattr(self, 'set_breadcrumb'): self.set_breadcrumb(
                    "Startseite > Hauptmenü > Schülerverwaltung > Buchlisten")
                if hasattr(self, 'set_page_title'): self.set_page_title("Klassen-Buchlisten")
                self.tab_buchlisten.refresh_dropdown_and_books()
        except Exception as e:
            print(f"Unsichtbar abgefangener Fehler beim Tab-Wechsel: {e}")