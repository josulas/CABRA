import sys
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg
import numpy as np

uiclass, baseclass = pg.Qt.loadUiType("template.ui")

class MainWindow(uiclass, baseclass):
    def __init__(self, data):
        super().__init__()
        self.setupUi(self)
        self.widget.plot(data, pen='red')
        self.widget.showGrid(x=True, y=True, alpha=0.3)

def run_ui(data):
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    app.exec()

if __name__ == '__main__':
    run_ui(data=np.linspace(0, 100, 10))
