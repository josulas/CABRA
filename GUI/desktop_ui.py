import sys
import os
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QProcess, Slot as pyqtSlot, Signal as pyqtSignal, QEventLoop
from pyqtgraph.exporters import ImageExporter
from pyqtgraph import mkPen
import numpy as np
from template_desktop import Ui_MainWindow
from playaudio import EarSelect, CLICK_DURATION, CYCLE_DURATION
from simserial import Actions

NCLICKS = 5
SAMPLINGRATE = 10_000  # Hz (DO NOT CHANGE)
OUTPUT_DIR = 'saved_audiometries'


class CABRA_Window(Ui_MainWindow, QMainWindow):
    # Define states
    STATE_IDLE = 0
    STATE_RUNNING = 1
    STATE_WAITING_FOR_USER = 2
    STATE_COMPLETED = 3

    # Class variables
    recording_completed = pyqtSignal()
    valid_amplitudes = list(range(-10, 45, 5))

    def __init__(self, process_path):
        # Initial setup
        super().__init__()
        self.setupUi(self)
        self.state = CABRA_Window.STATE_IDLE
        self.current_freq_idx = 0
        self.current_ear = EarSelect.LEFT
        self.in_CABRASweep = False

        # Pens
        self.evoked_pen = mkPen(color=(255, 0, 0), width=2)
        self.right_audiogram_pen = mkPen(color=(230, 97, 0), width=2, symbol='o')
        self.left_audiogram_pen = mkPen(color=(0, 0, 255), width=2, symbol='x')

        # Checkbone also modifies the pen, so we might as well set it up right now
        self.checkBone.stateChanged.connect(self.checkbone_changed)

        # Plot setup
        self.evoked_X_axis = np.linspace(0, CYCLE_DURATION, CYCLE_DURATION * SAMPLINGRATE // 1000)
        self.nulldata = np.zeros_like(self.evoked_X_axis)
        self.plotWidget.plot(self.evoked_X_axis, self.nulldata, pen=self.evoked_pen)
        self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
        self.audiogram_figure_ready = False

        # Amplitude setup, initialize to midpoint
        self.amplitudes = CABRA_Window.valid_amplitudes
        self.id_min = 0
        self.id_max = len(self.amplitudes) - 1
        self.id_mid = 1 # 0 [dbHL]
        self.dbamp = self.amplitudes[self.id_mid]

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
        self.pushRUN.clicked.connect(self.on_click_pushRUN)
        self.recording_completed.connect(self.handle_recording_completed)

        # pushEVOKED and pushNOISE are disabled until recording is completed
        self.pushEVOKED.clicked.connect(self.go_quieter)
        self.pushEVOKED.setEnabled(False)
        self.pushNOISE.clicked.connect(self.go_louder)
        self.pushNOISE.setEnabled(False)

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
        self.audiogram_left = np.ones(self.comboBoxFreq.count()) * np.nan
        self.audiogram_right = np.ones(self.comboBoxFreq.count()) * np.nan

        # Connect the CABRASweep button
        self.pushCABRASweep.clicked.connect(self.CABRASweep)

    def checkbone_changed(self):
        """
        Change the pen color for the evoked potential plot
        """
        if self.checkBone.isChecked():
            self.evoked_pen = mkPen(color=(0, 255, 0), width=2)
            self.right_audiogram_pen = mkPen(color=(230, 97, 0), width=2, symbol='.')
            self.left_audiogram_pen = mkPen(color=(0, 0, 255), width=2, symbol='.')
        else:
            self.evoked_pen = mkPen(color=(255, 0, 0), width=2)
            self.right_audiogram_pen = mkPen(color=(230, 97, 0), width=2, symbol='o')
            self.left_audiogram_pen = mkPen(color=(0, 0, 255), width=2, symbol='x')

    def change_max_click_duration(self):
        """
        Click duration must be smaller that cycle duration
        Modify the minimum value of the click duration spinbox accordingly
        """
        self.spinClickDuration.setMaximum(self.spinCycleDuration.value())

    ##################################################################################################
    # The following methods are related to the communication with the process and the GUI operation #
    ##################################################################################################

    def get_ear_selection(self):
        """
        Translate the radio buttons to the EarSelect enum
        """
        return EarSelect.LEFT if self.radioLeftEAR.isChecked() \
            else EarSelect.RIGHT if self.radioRightEAR.isChecked() \
            else EarSelect.BOTH

    def get_msg(self):
        """
        Get the message to send to the process, of the form
        RECORD nclicks freq_idx ear dbamp click_duration cycle_duration
        """
        ear = self.get_ear_selection()
        freq_idx = self.comboBoxFreq.currentIndex()
        dbamp = self.dbamp
        nclicks = self.nclicks
        click_duration = self.spinClickDuration.value()
        cycle_duration = self.spinCycleDuration.value()
        return f"{Actions.RECORD} {nclicks} {freq_idx} {ear} {dbamp} {click_duration} {cycle_duration} \n"

    def start_process(self):
        """
        Initialize the process to communicate with the ESP board (or simulation) script
        """
        self.process.start("python", [self.process_path])
        started = self.process.waitForStarted(500)
        if not started:
            self.labelStatus.setText("Failed to start process.")
            sys.exit(1)

        # Automatically read stdout and stderr when something new shows up
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

    def _print_msg(self):
        """
        Just for debugging purposes
        """
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

    ##############################################################################################
    # The following methods are related to the audiometry test, and the audiogram plotting/saving #
    ##############################################################################################

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

    def save_audiogram(self):
        """
        Save the audiogram to a .csv file, and its plot as a .png
        """
        audiogram = np.array([self.audiogram_left, self.audiogram_right])
        fname = f"{self.nameEdit.text()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        np.savetxt(os.path.join(OUTPUT_DIR, f"{fname}.csv"), audiogram, delimiter=',')

        # Save the audiogram plot
        if self.audiogram_figure_ready:
            size = self.plotWidget.size()
            exporter = ImageExporter(self.plotWidget.plotItem)
            exporter.parameters()['width'] = size.width()
            exporter.parameters()['height'] = size.height()
            exporter.export(os.path.join(OUTPUT_DIR, f"{fname}.png"))
            self.audiogram_figure_ready = False

        self.labelStatus.setText(f"Audiogram saved to {fname}")

    def plot_null(self):
        """
        Plot a null graph
        """
        self.plotWidget.clear()
        self.plotWidget.plot(self.evoked_X_axis, self.nulldata, pen=self.evoked_pen)
        self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
        self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

    def plot_evoked(self):
        """
        Plot the evoked potential
        """
        if self.filepath:
            evoked = np.load(self.filepath)
            self.plotWidget.clear()
            self.plotWidget.plot(self.evoked_X_axis, evoked, pen=self.evoked_pen)
            self.plotWidget.setXRange(0, CYCLE_DURATION, padding=0.)
            self.plotWidget.showGrid(x=True, y=True, alpha=0.3)

    def plot_audiogram(self):
        """
        Plot the audiogram once it's finished. The 'save_audiogram' shoud be saved right after this function.
        """
        # Plotting
        self.plotWidget.clear()
        self.plotWidget.plot(self.audiogram_left, pen='green', symbol='o', name='Left Ear')
        self.plotWidget.plot(self.audiogram_right, pen='blue', symbol='x', name='Right Ear')
        self.plotWidget.setXRange(0, len(self.audiogram_left) - 1, padding=0.05)
        self.plotWidget.setTitle(f"Audiogram for {self.nameEdit.text()}")

        # Axis setup
        ax = self.plotWidget.getAxis('bottom')
        ax.setTicks([[(i, str(self.comboBoxFreq.itemText(i))) for i in range(len(self.audiogram_left))]])
        ax.setLabel('Frequency [Hz]')
        ay = self.plotWidget.getAxis('left')
        ay.setLabel('Amplitude [dB HL]')
        self.plotWidget.addLegend()

        # Update the audiogram's save status
        self.audiogram_figure_ready = True

    ##############################################################################################
    # The following methods are related to the actual audiometry test, and the trademark CABRASweep #
    ##############################################################################################

    def reset_dbamp(self):
        """
        Reset the amplitude range to the initial state
        """
        self.id_min = 0
        self.id_max = len(self.amplitudes) - 1
        self.id_mid = 1  # 0 [dbHL] is at position 1, always
        self.dbamp = self.amplitudes[self.id_mid]

    def update_mid_dbapm(self):
        """
        Update the amplitude to the midpoint of the current range. Keep track of the last amplitude.
        """
        self.id_mid = (self.id_min + self.id_max) // 2
        self.dbamp = self.amplitudes[self.id_mid]

    def go_quieter(self):
        """
        This method is called when the user indicates that the sound was heard.
        It will update the amplitude range, and perform the next audiometry test.
        Notice that the method updated the midpoint in a binary search fashion.
        This method is called by the pushEVOKED button
        """
        self.id_max = self.id_mid
        self.continue_audiometry_test()

    def go_louder(self):
        """
        Analogous to the go_quieter method, but for when the sound was not heard.
        It will update the amplitude range, and perform the next audiometry test.
        This method is called by the pushNOISE button
        """
        self.id_min = self.id_mid + 1
        self.continue_audiometry_test()

    def continue_audiometry_test(self):
        """
        The recursive step in the audiometry test algorithm, triggerd by either the pushEVOKED or pushNOISE buttons.
        """
        if self.id_min < self.id_max:
            self.update_mid_dbapm()
            self.state = CABRA_Window.STATE_RUNNING
        else:
            self.state = CABRA_Window.STATE_COMPLETED
        self.perform_audiometry_test()

    def on_click_pushRUN(self):
        """
        Activate the RUNNING state, and perform audiometry. Make sure CABRASweep is not running beforehand
        """
        self.in_CABRASweep = False
        self.state = CABRA_Window.STATE_RUNNING
        self.perform_audiometry_test()

    def perform_audiometry_test(self):
        """
        For a given frequency and ear, perform the audiometry test to detect the hearing threshold,
        by varying the amplitude of the sound stimulus and recording the evoked potential.

        NOTE: This function is recursive, and will call itself until the audiometry test is completed.
        """

        if self.state == CABRA_Window.STATE_RUNNING:
            # Record ABR for the current amplitude
            self.pushRUN.setEnabled(False)
            self.start_recording()
            self.state = CABRA_Window.STATE_WAITING_FOR_USER

        elif self.state == CABRA_Window.STATE_WAITING_FOR_USER:
            # Wait for the user to indicate if the sound was heard (handled by pushEVOKED and pushNOISE)
            # For further clarification, refer to the go_quieter and go_louder methods.
            pass

        elif self.state == CABRA_Window.STATE_COMPLETED:
            # Reset the state
            self.complete_current_test()

    def complete_current_test(self):
        """
        This method is called once the binary search performed in 'perform_audiometry_test' has converged.
        It will update the audiogram and reset the amplitude range.
        If the CABRASweep is active, it will move on to the next test.
        """

        # Disable the evoked/noise buttons
        self.pushEVOKED.setEnabled(False)
        self.pushNOISE.setEnabled(False)
        self.pushRUN.setEnabled(True)

        # Update the status label and the audiogram
        frequency = self.comboBoxFreq.currentText()
        ear = 'left' if self.radioLeftEAR.isChecked() else 'right' if self.radioRightEAR.isChecked() else 'both'
        self.labelStatus.setText(f"Hearing threshold for {ear} ear at frequency = {frequency} [Hz]:"
                                 f" {self.dbamp} [dbHL]")

        # Update the audiogram threshold level for the relevant frequency
        if ear == 'left':
            self.audiogram_left[self.comboBoxFreq.currentIndex()] = self.dbamp
        elif ear == 'right':
            self.audiogram_right[self.comboBoxFreq.currentIndex()] = self.dbamp

        self.reset_dbamp()

        # Check if the audiogram is ready to be saved
        if self.audiogram_is_ready():
            self.audiogram_ready_popup()
            self.plot_audiogram()
            self.save_audiogram()
        else:
            self.plot_null()

        # Continue the CABRASweep if necessary
        if self.in_CABRASweep:
            self.move_to_next_test()

    def move_to_next_test(self):
        """
        Move to the next test in the CABRASweep, by updating ear and frequency.
        If done, finish the CABRASweep.
        """

        assert self.in_CABRASweep

        # Swap ears, or move to the next frequency
        if self.current_ear == EarSelect.LEFT:
            self.current_ear = EarSelect.RIGHT
        else:
            self.current_ear = EarSelect.LEFT
            self.current_freq_idx += 1

        # If there are more tests to perform
        if self.current_freq_idx < self.comboBoxFreq.count():
            # The next few lines, though scary looking, only update the input widgets to the next test
            self.comboBoxFreq.setCurrentIndex(self.current_freq_idx)
            if self.current_ear == EarSelect.LEFT:
                self.radioLeftEAR.setChecked(True)
            elif self.current_ear == EarSelect.RIGHT:
                self.radioRightEAR.setChecked(True)

            # Perform the next test
            self.state = CABRA_Window.STATE_RUNNING
            self.perform_audiometry_test()

        # Finish off the CABRASweep
        else:
            self.state = CABRA_Window.STATE_IDLE
            self.labelStatus.setText("CABRASweep completed.")
            for widget in [self.pushCABRASweep, self.pushRUN, self.spinClickDuration,
                           self.spinCycleDuration, self.checkBone, self.nameEdit,
                           self.dateEdit, self.lineID]:
                widget.setEnabled(True)
            self.in_CABRASweep = False

    # da GOAT
    def CABRASweep(self):
        """
        Sweep over all frequencies and ears to perform the audiometry test.
        This function relies heavily on the recursive function 'perform_audiometry_test', as well
        as the 'move_to_next_test' function.
        """

        assert self.state == CABRA_Window.STATE_IDLE and self.in_CABRASweep == False
        self.in_CABRASweep = True

        # Disable all widgets that shouldn't be touched
        for widget in [self.pushCABRASweep, self.pushRUN, self.spinClickDuration,
                       self.spinCycleDuration, self.checkBone, self.nameEdit,
                       self.dateEdit, self.lineID]:
            widget.setEnabled(False)

        # Initialize the test
        self.current_freq_idx = 0
        self.current_ear = EarSelect.LEFT
        self.state = CABRA_Window.STATE_RUNNING
        self.perform_audiometry_test()

    def closeEvent(self, event):
        """
        Kill the process when the window is closed
        """
        self.process.kill()
        event.accept()


def run_ui():
    app = QApplication(sys.argv)
    window = CABRA_Window(process_path='simserial.py')
    window.show()
    app.exec()


if __name__ == '__main__':
    run_ui()
