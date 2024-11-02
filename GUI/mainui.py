import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg
import numpy as np
from template import Ui_MainWindow
from playaudio import Clicker, EarSelect, CLICK_DURATION, CYCLE_DURATION, NCLICKS
from simserial import Actions


class MainWindow(Ui_MainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushRUN.clicked.connect(self._print_msg)

    def get_ear_selection(self):
        return EarSelect.LEFT if self.radioLeftEAR.isChecked() \
            else EarSelect.RIGHT if self.radioRightEAR.isChecked() \
            else EarSelect.BOTH

    def get_msg(self):
        ear = self.get_ear_selection()
        freq_idx = self.comboBoxFreq.currentIndex()
        dbamp = int(self.comboBoxAmp.currentText())
        return f"{Actions.RECORD} {NCLICKS} {freq_idx} {ear} {dbamp} {CLICK_DURATION} {CYCLE_DURATION}"

    def _print_msg(self):
        print(self.get_msg())


def run_ui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    run_ui()
