import os
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
    done = False
    data = np.zeros(1)
    base_dir = 'saved_data'
    paths = os.listdir(base_dir)
    path_str = '\n'.join([f"{i}: {path}" for (i, path) in enumerate(paths)])
    print('Valid paths:') 
    print(path_str)

    while not done:
        choice = input('Select path: ')
        try:
            path = paths[int(choice)]
            print(f"You chose: {path}")
            data = np.load(os.path.join(base_dir, path))
            done = True
        except (FileNotFoundError, ValueError):
            print('Invalid file. Try again')

    print(data.shape)
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
