import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QProcess, pyqtSlot, pyqtSignal
import pyqtgraph as pg
import numpy as np
from template import Ui_MainWindow
from playaudio import Clicker, EarSelect, CLICK_DURATION, CYCLE_DURATION, NCLICKS
from simserial import Actions


SAMPLINGRATE = 10_000  # Hz (DO NOT CHANGE)


class MainWindow(Ui_MainWindow, QMainWindow):
    recording_completed = pyqtSignal()

    def __init__(self, process_path):
        super().__init__()
        self.setupUi(self)

        # Plot setup
        self.evoked_X_axis = np.linspace(0, CYCLE_DURATION, CYCLE_DURATION * SAMPLINGRATE // 1000)
        self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

        # Filepath to store the recording
        self.filepath = ''

        # Process communication setup
        self.process = QProcess(self)
        self.process_path = process_path
        self.start_process()
        self.pushRUN.clicked.connect(self.start_recording)
        self.recording_completed.connect(self.plot_evoked)

    def get_ear_selection(self):
        return EarSelect.LEFT if self.radioLeftEAR.isChecked() \
            else EarSelect.RIGHT if self.radioRightEAR.isChecked() \
            else EarSelect.BOTH

    def get_msg(self):
        ear = self.get_ear_selection()
        freq_idx = self.comboBoxFreq.currentIndex()
        dbamp = int(self.comboBoxAmp.currentText())
        return f"{Actions.RECORD} {NCLICKS} {freq_idx} {ear} {dbamp} {CLICK_DURATION} {CYCLE_DURATION} \n"

    def start_process(self):
        self.process.start("python", [self.process_path])
        started = self.process.waitForStarted(500)
        if not started:
            self.labelStatus.setText("Failed to start process.")
            sys.exit(1)
        self.handle_stderr()

    def _print_msg(self):
        print(self.get_msg())

    @pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        if '.npy' in data:
            self.filepath = data.strip()
            self.labelStatus.setText(f"Recording completed and stored at {self.filepath}")
            self.recording_completed.emit()
        else:
            self.handle_stderr()

    @pyqtSlot()
    def handle_stderr(self):
        output = self.process.readAllStandardError().data().decode()
        if output == '1':
            self.labelStatus.setText("Connection error occurred.")
        elif output == '2':
            self.labelStatus.setText("Runtime error occurred.")
        elif output == '3':
            self.labelStatus.setText("Value error occurred.")

    @pyqtSlot()
    def start_recording(self):
        ear = 'left' if self.radioLeftEAR.isChecked() else 'right' if self.radioRightEAR.isChecked() else 'both'
        self.labelStatus.setText(f"Recording for {ear} ear{'s' if ear == 'both' else ''}, "
                                 f"frequency {self.comboBoxFreq.currentText()} Hz, "
                                 f"amplitude {self.comboBoxAmp.currentText()} dB, ")
        self.process.write(self.get_msg().encode())
        # Wait for the process to write the file, and read the filepath from stdout
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

    def plot_evoked(self):
        if self.filepath:
            evoked = np.load(self.filepath)
            self.plotWidget.clear()
            self.plotWidget.plot(self.evoked_X_axis, evoked, pen='red')

    # Kill the process when the window is closed
    def closeEvent(self, event):
        self.process.kill()
        event.accept()


def run_ui():
    app = QApplication(sys.argv)
    window = MainWindow(process_path='simserial.py')
    window.show()
    app.exec()


if __name__ == '__main__':
    run_ui()
