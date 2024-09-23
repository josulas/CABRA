import sys
from PySide6.QtWidgets import QApplication
import pyqtgraph as pg

uiclass, baseclass = pg.Qt.loadUiType("template.ui")

class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.widget.plot([10, 100, 1000, 10000],
                         [4, 5, 4, 3],
                         pen='red',
                         symbol='x')
        self.widget.setLogMode(True)
        ax = self.widget.getAxis('bottom')
        #ax.setTicks([[10, 100, 1000, 10000]])
        self.widget.showGrid(x=True, y=True, alpha=0.3)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
