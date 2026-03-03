import sys
from PyQt6.QtWidgets import QApplication
from MainWindow import MainWindow
from loading_gate import LoadingGate

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow()

    def open_main():
        main_window.show()

    gate = LoadingGate(on_success=open_main)  # liest .env automatisch neben Main.py
    gate.show()

    sys.exit(app.exec())

