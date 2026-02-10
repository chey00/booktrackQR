from PyQt6.QtWidgets import QMainWindow

from CentralWidget import CentralWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        central_widget = CentralWidget(self)

        self.setCentralWidget(central_widget)
#Mustafa
        self.setWindowTitle("BooktrackQR")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("QWidget { background-color: white; }")