import sys
from PySide6.QtWidgets import QApplication
import pyqtgraph as pg
import numpy as np

uiclass, baseclass = pg.Qt.loadUiType("template.ui")

class MainWindow(uiclass, baseclass):
    def __init__(self, data):
        super().__init__()
        self.setupUi(self)
        self.widget.plot(data, pen='red')
        self.widget.showGrid(x=True, y=True, alpha=0.3)

def main():
    app = QApplication(sys.argv)
    window = MainWindow(data=np.linspace(0, 100, 10))
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
