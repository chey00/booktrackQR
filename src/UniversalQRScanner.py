# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: UniversalQRScanner.py
# Autorin: Jaclyn Barta (Maerz 2026)

# Zweck: Universelle Kamera-Validierung ohne Umlaut-Probleme (OpenCV Hershey Fonts)
# ------------------------------------------------------------------------------

import cv2
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from database_manager import DatabaseManager


class UniversalQRScanner(QDialog):
    def __init__(self, parent=None, target_mode="STUDENT", color_theme="#008781", context_text="Scan"):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.target_mode = target_mode  # "STUDENT" oder "BOOK"
        self.color_theme = color_theme  # Rahmenfarbe fuer Ausleihe (Gruen) / Rueckgabe (Rot)
        self.context_text = context_text
        self.final_result = None
        self.error_active = False

        self.setWindowTitle(f"BooktrackQR - {self.context_text}")
        self.setFixedSize(800, 600)
        layout = QVBoxLayout(self)
        self.video_label = QLabel("Kamera wird gestartet...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label)

        # Kamera-Initialisierung
        self.cap = cv2.VideoCapture(0)
        self.detector = cv2.QRCodeDetector()

        # Timer fuer fluesssiges Kamerabild (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret: return
        data, bbox, _ = self.detector.detectAndDecode(frame)

        # BGR Farben fuer OpenCV (Gruen vs. Rot-Ton)
        main_color = (0, 255, 0) if self.color_theme == "#8DBF42" else (104, 115, 229)

        if data and not self.error_active:
            self.process_scan(data, frame, main_color)

        # Text-Position optimiert (30, 80) und Umlaute umschrieben
        cv2.putText(frame, self.context_text, (150, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, main_color, 2)

        # Umwandlung fuer die Anzeige in PyQt6
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def process_scan(self, data, frame, color):
        """Validierung des Scans gegen die Datenbank (Jaclyn Barta)"""
        is_book = data.startswith("BOOK|")
        is_student = data.startswith("MB_")

        # 1. Format-Pruefung
        if self.target_mode == "STUDENT" and not is_student:
            self.trigger_error("FALSCHER QR (Kein Schueler!)")
            return
        elif self.target_mode == "BOOK" and not is_book:
            self.trigger_error("FALSCHER QR (Kein Buch!)")
            return

        # 2. Datenbank-Abgleich
        if is_student:
            student = self.db.get_student_by_qr_id(data)
            if student:
                self.final_result = student
                self.close_with_success()
            else:
                self.trigger_error("SCHUELER UNBEKANNT!")

        elif is_book:
            parts = data.split('|')
            isbn = parts[1]

            # PBI Erfuellung: Warnung bei bereits verliehenen Buechern (nur in Ausleihe)
            if self.target_mode == "BOOK" and "Ausleihe" in self.context_text:
                loaner = self.db.get_current_loaner(isbn)
                if loaner:
                    self.trigger_error(f"BEREITS VERLIEHEN AN: {loaner.upper()}")
                    return

            book = self.db.get_book_by_qr_data(isbn)
            if book:
                book['exemplar_nr'] = parts[2] if len(parts) > 2 else "001"
                self.final_result = book
                self.close_with_success()
            else:
                self.trigger_error("BUCH NICHT GEFUNDEN!")

    def trigger_error(self, text):
        """Fehlermeldung im Live-Bild (Jaclyn Barta)"""
        self.error_active = True
        self.video_label.setStyleSheet("border: 10px solid red;")
        # Scanner bleibt offen, blockiert aber kurz fuer neuen Versuch
        QTimer.singleShot(2000, self.reset_error)

    def reset_error(self):
        self.error_active = False
        self.video_label.setStyleSheet("")

    def close_with_success(self):
        self.timer.stop()
        self.cap.release()
        self.accept()

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        super().closeEvent(event)