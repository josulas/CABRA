import sys
from PySide6.QtWidgets import QApplication
import pyqtgraph as pg

uiclass, baseclass = pg.Qt.loadUiType("template.ui")

class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        freqs = [10, 100, 1000, 10000]
        self.widget.plot(freqs,
                         [4, 5, 4, 3],
                         pen='red',
                         symbol='x')
        self.widget.setLogMode(x=True, y=False)
        self.widget.setXRange(1, 4)
        self.widget.showGrid(x=True, y=True, alpha=0.3)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
