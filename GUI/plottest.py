import numpy as np
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
import pyqtgraph as pg

CLICK_DURATION = 30 # ms

class MainWindow(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.widget = pg.PlotWidget()
        self.time = np.linspace(0, CLICK_DURATION, len(data))
        self.setCentralWidget(self.widget)
        self.widget.plot(self.time, data, pen='red')
        # self.widget.setYRange(-200, 200, padding=0.5)
        self.widget.showGrid(x=True, y=True, alpha=0.3)
        
def main():
    data = np.load('evoked_test.npy')
    print(data.shape)
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
