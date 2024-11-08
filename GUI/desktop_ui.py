import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QProcess, Slot as pyqtSlot, Signal as pyqtSignal
import numpy as np
from template_desktop import Ui_MainWindow
from playaudio import Clicker, EarSelect, CLICK_DURATION, CYCLE_DURATION
from simserial import Actions

NCLICKS = 5
SAMPLINGRATE = 10_000  # Hz (DO NOT CHANGE)


class MainWindow(Ui_MainWindow, QMainWindow):
    recording_completed = pyqtSignal()
    valid_amplitudes = list(range(-10, 50, 10))

    def __init__(self, process_path):
        super().__init__()
        self.setupUi(self)

        # Plot setup
        self.evoked_X_axis = np.linspace(0, CYCLE_DURATION, CYCLE_DURATION * SAMPLINGRATE // 1000)
        self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

        # Amplitude setup, initialize to midpoint
        self.amplitudes = MainWindow.valid_amplitudes
        self.dbamp = self.amplitudes[len(self.amplitudes) // 2]

        # Clicker init config
        self.spinClickDuration.setValue(CLICK_DURATION)
        self.spinCycleDuration.setValue(CYCLE_DURATION)
        # Update maximum click duration based on cycle duration
        self.spinCycleDuration.valueChanged.connect(self.change_max_click_duration)

        # Filepath to store the recording
        self.filepath = ''

        # Process communication setup
        self.process = QProcess(self)
        self.process_path = process_path
        self.start_process()
        self.pushRUN.clicked.connect(self.perform_audiometry_test)
        self.recording_completed.connect(self.plot_evoked)

    def change_max_click_duration(self):
        """
        Click duration must be smaller that cycle duration
        Modify the minimum value of the click duration spinbox accordingly
        """
        self.spinClickDuration.setMaximum(self.spinCycleDuration.value())

    def get_ear_selection(self):
        return EarSelect.LEFT if self.radioLeftEAR.isChecked() \
            else EarSelect.RIGHT if self.radioRightEAR.isChecked() \
            else EarSelect.BOTH

    def get_msg(self):
        ear = self.get_ear_selection()
        freq_idx = self.comboBoxFreq.currentIndex()
        dbamp = self.dbamp
        click_duration = self.spinClickDuration.value()
        cycle_duration = self.spinCycleDuration.value()
        return f"{Actions.RECORD} {NCLICKS} {freq_idx} {ear} {dbamp} {click_duration} {cycle_duration} \n"

    def start_process(self):
        self.process.start("python", [self.process_path])
        # started = self.process.waitForStarted(500)
        # if not started:
        #     self.labelStatus.setText("Failed to start process.")
        #     sys.exit(1)
        self.handle_stderr()

    def _print_msg(self):
        print(self.get_msg())

    @pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        print(data)
        if '.npy' in data:
            self.filepath = data.strip()
            self.labelStatus.setText(f"Recording completed and stored at {self.filepath}")
            self.recording_completed.emit()
        else:
            self.handle_stderr()

    @pyqtSlot()
    def handle_stderr(self):
        output = self.process.readAllStandardError().data().decode()
        print(output)
        # Connection error: popout window for user to check connection
        if output == '1':
            self.labelStatus.setText("Connection error occurred.")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText("Connection error occurred.")
            msg_box.setInformativeText("The process will be restarted.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.buttonClicked.connect(self.start_process)
            msg_box.exec()

        elif output == '2':
            self.labelStatus.setText("Runtime error occurred.")
        elif output == '3':
            self.labelStatus.setText("Value error occurred.")

    @pyqtSlot()
    def start_recording(self):
        ear = 'left' if self.radioLeftEAR.isChecked() else 'right' if self.radioRightEAR.isChecked() else 'both'
        self.labelStatus.setText(f"Recording for {ear} ear{'s' if ear == 'both' else ''}, "
                                 f"frequency {self.comboBoxFreq.currentText()} Hz, "
                                 f"amplitude {self.dbamp} dB, ")
        self.process.write(self.get_msg().encode())
        # Wait for the process to write the file, and read the filepath from stdout
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

    def perform_audiometry_test(self):
        """
        For a given frequency and ear, perform the audiometry test to detect the hearing threshold,
        by varying the amplitude of the sound stimulus and recording the evoked potential.
        """
        id_min = 0
        id_max = len(self.amplitudes) - 1
        while id_min < id_max:
            mid = (id_min + id_max) // 2
            self.dbamp = self.amplitudes[mid]
            self.start_recording()
            # Wait for the recording to complete
            if self.filepath:
                id_min = mid + 1
            else:
                id_max = mid

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
