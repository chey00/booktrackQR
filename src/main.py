import sys
from PyQt6.QtWidgets import QApplication
from MainWindow import MainWindow
from loading_gate import LoadingGate

main_window = None

if __name__ == '__main__':
    app = QApplication(sys.argv)

    def open_main(cfg: dict):
        global main_window
        main_window = MainWindow(cfg)
        main_window.show()

    gate = LoadingGate(on_success=open_main)
    gate.show()

    sys.exit(app.exec())
