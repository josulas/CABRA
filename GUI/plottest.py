import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = pg.PlotWidget()
        freqs = [10, 100, 1000, 10000]
        self.setCentralWidget(self.widget)
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
