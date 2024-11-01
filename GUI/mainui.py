import sys
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg
import numpy as np
from template import Ui_MainWindow


class MainWindow(Ui_MainWindow):
    def __init__(self, data):
        super().__init__()
        self.setupUi(self)
        self.plotWidget.plot(data, pen='red')
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

def run_ui(data):
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    app.exec()

if __name__ == '__main__':
    run_ui(data=np.linspace(0, 100, 10))
