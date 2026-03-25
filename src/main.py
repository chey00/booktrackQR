import sys
from PyQt6.QtWidgets import QApplication
from mainWindow import MainWindow
from loading_gate import LoadingGate

def start_app():
    app = QApplication(sys.argv)
    main_window = None

    def open_main():
        nonlocal main_window
        main_window = MainWindow(db_config=gate.cfg)
        main_window.showFullScreen()

    gate = LoadingGate(on_success=open_main)
    gate.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    start_app()