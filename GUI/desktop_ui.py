import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QProcess, Slot as pyqtSlot, Signal as pyqtSignal, QEventLoop
import numpy as np
from template_desktop import Ui_MainWindow
from playaudio import EarSelect, CLICK_DURATION, CYCLE_DURATION
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
        self.nulldata = np.zeros_like(self.evoked_X_axis)
        self.plotWidget.plot(self.evoked_X_axis, self.nulldata, pen='red')
        self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

        # Amplitude setup, initialize to midpoint
        self.amplitudes = MainWindow.valid_amplitudes
        self.id_min = 0
        self.id_max = len(self.amplitudes) - 1
        self.id_mid = (self.id_min + self.id_max) // 2
        self.dbamp = self.amplitudes[self.id_mid]
        self.prev_dbamp = self.dbamp

        # Clicker init config
        self.nclicks = NCLICKS
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
        self.recording_completed.connect(self.handle_recording_completed)

        # pushEVOKED and pushNOISE are disabled until recording is completed
        self.pushEVOKED.clicked.connect(self.set_heard)
        self.pushEVOKED.setEnabled(False)
        self.pushNOISE.clicked.connect(self.set_not_heard)
        self.pushNOISE.setEnabled(False)
        self.heard = False

        # Customize color for pushEVOKED and pushNOISE when disabled (set to gray)
        self.pushEVOKED.setStyleSheet("""
            QPushButton:disabled { background-color: gray; }
            QPushButton { background-color: rgb(131, 153, 105); }
        """)
        self.pushNOISE.setStyleSheet("""
            QPushButton:disabled { background-color: gray; }
            QPushButton { background-color: rgb(199, 122, 108); }
        """)

        # Initialize audiograms as nan arrays
        self.audiogram_left = np.ones(self.comboBoxFreq.count())*np.nan
        self.audiogram_right = np.ones(self.comboBoxFreq.count())*np.nan

    def change_max_click_duration(self):
        """
        Click duration must be smaller that cycle duration
        Modify the minimum value of the click duration spinbox accordingly
        """
        self.spinClickDuration.setMaximum(self.spinCycleDuration.value())

    def update_mid_dbapm(self):
        self.prev_dbamp = self.dbamp
        self.id_mid = (self.id_min + self.id_max) // 2
        self.dbamp = self.amplitudes[self.id_mid]

    def set_heard(self):
        self.heard = True
        self.id_max = self.id_mid
        self.update_mid_dbapm()
        self.perform_audiometry_test()

    def set_not_heard(self):
        self.heard = False
        self.id_min = self.id_mid + 1
        self.update_mid_dbapm()
        self.perform_audiometry_test()  # ugliest recursion ever

    def get_ear_selection(self):
        return EarSelect.LEFT if self.radioLeftEAR.isChecked() \
            else EarSelect.RIGHT if self.radioRightEAR.isChecked() \
            else EarSelect.BOTH

    def get_msg(self):
        ear = self.get_ear_selection()
        freq_idx = self.comboBoxFreq.currentIndex()
        dbamp = self.dbamp
        nclicks = self.nclicks
        click_duration = self.spinClickDuration.value()
        cycle_duration = self.spinCycleDuration.value()
        return f"{Actions.RECORD} {nclicks} {freq_idx} {ear} {dbamp} {click_duration} {cycle_duration} \n"

    def start_process(self):
        self.process.start("python", [self.process_path])
        started = self.process.waitForStarted(500)
        if not started:
            self.labelStatus.setText("Failed to start process.")
            sys.exit(1)

        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

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
            msg_box.setText("Connection error occurred.")
            msg_box.setInformativeText("Please check the connection and try again.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.buttonClicked.connect(self.start_process)
            msg_box.exec()

        elif output == '2':
            self.labelStatus.setText("Runtime error occurred.")
        elif output == '3':
            self.labelStatus.setText("Value error occurred.")

    # @pyqtSlot()
    def start_recording(self):
        self.pushEVOKED.setEnabled(False)
        self.pushNOISE.setEnabled(False)
        ear = 'left' if self.radioLeftEAR.isChecked() else 'right' if self.radioRightEAR.isChecked() else 'both'
        self._print_msg()
        self.labelStatus.setText(f"Recording for {ear} ear{'s' if ear == 'both' else ''}, "
                                 f"frequency {self.comboBoxFreq.currentText()} Hz, "
                                 f"amplitude {self.dbamp} dB, ")
        self.process.write(self.get_msg().encode())

    def handle_recording_completed(self):
        # Update status
        self.labelStatus.setText(f"Recording completed and stored at {self.filepath}. Indicate if the sound was heard.")
        # Set pushNOISE and pushEVOKED to be enabled
        self.pushEVOKED.setEnabled(True)
        self.pushNOISE.setEnabled(True)
        # Plot
        self.plot_evoked()

    def audiogram_is_ready(self):
        """
        Check if the audiogram is ready to be saved
        """
        return not np.isnan(self.audiogram_left).any() and not np.isnan(self.audiogram_right).any()

    @staticmethod
    def audiogram_ready_popup():
        """
        Popup window to indicate that the audiogram is ready
        """
        msg_box = QMessageBox()
        msg_box.setText("Audiogram is ready.")
        msg_box.setInformativeText("The audiogram is ready to be saved.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def perform_audiometry_test(self):
        """
        For a given frequency and ear, perform the audiometry test to detect the hearing threshold,
        by varying the amplitude of the sound stimulus and recording the evoked potential.
        """

        if self.id_min < self.id_max:
            self.pushRUN.setEnabled(False)
            self.start_recording()

        else:
            # Disable the evoked/noise buttons
            self.pushEVOKED.setEnabled(False)
            self.pushNOISE.setEnabled(False)
            self.pushRUN.setEnabled(True)

            # Update the status label and the audiogram
            frequency = self.comboBoxFreq.currentText()
            ear = 'left' if self.radioLeftEAR.isChecked() else 'right' if self.radioRightEAR.isChecked() else 'both'
            self.labelStatus.setText(f"Hearing threshold for {ear} ear at frequency = {frequency} [Hz]:"
                                     f" {self.prev_dbamp} [dbHL]")

            if ear == 'left':
                self.audiogram_left[self.comboBoxFreq.currentIndex()] = self.prev_dbamp
            elif ear == 'right':
                self.audiogram_right[self.comboBoxFreq.currentIndex()] = self.prev_dbamp


            # Reset the amplitude range
            self.id_min = 0
            self.id_max = len(self.amplitudes) - 1
            self.id_mid = (self.id_min + self.id_max) // 2
            self.dbamp = self.amplitudes[self.id_mid]

            # Check if the audiogram is ready to be saved
            print(self.audiogram_left)
            print(self.audiogram_right)
            if self.audiogram_is_ready():
                self.audiogram_ready_popup()
                self.plot_audiogram()
            else:
                self.plotWidget.clear()
                self.plotWidget.plot(self.evoked_X_axis, self.nulldata, pen='red')

    def plot_evoked(self):
        if self.filepath:
            evoked = np.load(self.filepath)
            self.plotWidget.clear()
            self.plotWidget.plot(self.evoked_X_axis, evoked, pen='red')
            self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)

    def plot_audiogram(self):
        self.plotWidget.clear()
        self.plotWidget.plot(self.audiogram_left, pen='green', symbol='o', name='Left Ear')
        self.plotWidget.plot(self.audiogram_right, pen='blue', symbol='x', name='Right Ear')
        self.plotWidget.setXRange(0, len(self.audiogram_left) - 1, padding=0.)
        ax = self.plotWidget.getAxis('bottom')
        ax.setTicks([[(i, str(self.comboBoxFreq.itemText(i))) for i in range(len(self.audiogram_left))]])
        ax.setLabel('Frequency [Hz]')
        ay = self.plotWidget.getAxis('left')
        ay.setLabel('Amplitude [dB HL]')
        self.plotWidget.addLegend()
        self.labelStatus.setText("Audiogram is ready to be saved.")

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
