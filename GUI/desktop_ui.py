# System level imports
import sys
import os
from datetime import datetime
from time import sleep

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QStyle, QDialogButtonBox
from PySide6.QtCore import QProcess, Slot as pyqtSlot, Signal as pyqtSignal
from PySide6.QtGui import QShortcut, QKeySequence, QIcon
from PySide6 import QtGui, QtCore
from pyqtgraph.exporters import ImageExporter
# Plotting related imports
from pyqtgraph import mkPen
import numpy as np
# Local imports
from ui_templates.dialog_reconnect import Ui_DialogReconnect
from ui_templates.dialog_tone_burst import Ui_DialogToneBurst
from ui_templates.template_desktop import Ui_MainWindow
from clicker import EarSelect
from desktop_serial import Actions, SAMPLINGRATE

OUTPUT_DIR = 'saved_audiometries'
PEAK_TO_PEAK_EVOKED = 1000  # [uV]
DEFAULT_NCLICKS = 500
DEFAULT_CLICK_DURATION = 10
DEFAULT_CYCLE_DURATION = 30


class CABRA_Window(Ui_MainWindow, QMainWindow):
    # Define states
    STATE_IDLE = 0
    STATE_RUNNING = 1
    STATE_WAITING_FOR_USER = 2
    STATE_COMPLETED = 3

    # Class variables
    recording_completed = pyqtSignal()
    valid_amplitudes = list(range(-10, 45, 5))

    # Process paths for every mode
    process_paths = {'simulation': 'simserial.py', 'CABRA device': 'desktop_serial.py'}

    def __init__(self):
        # Initial setup
        super().__init__()
        self.setWindowIcon(QIcon('cabra.ico'))
        self.setupUi(self)
        self.state = CABRA_Window.STATE_IDLE
        self.current_freq_idx = 0
        self.current_ear = EarSelect.LEFT
        self.in_CABRASweep = False

        # Inital clicker configuration
        self.n_clicks = DEFAULT_NCLICKS
        self.click_duration = DEFAULT_CLICK_DURATION
        self.cycle_duration = DEFAULT_CYCLE_DURATION
        self.actionTone_burst.triggered.connect(self.show_tone_burst_dialog)
        self.n_reps = 0 # Number of repetitions for a given test

        # Pens
        self.evoked_pen = mkPen(color=(255, 0, 0), width=2)
        self.right_audiogram_pen = mkPen(color=(230, 97, 0), width=3)
        self.right_audiogram_symbol = {'symbol': 'o',
                                       'symbolPen': (230, 97, 0),
                                       'symbolBrush': (230, 97, 0),
                                       'symbolSize': 10}
        self.left_audiogram_pen = mkPen(color=(0, 0, 255), width=3)
        self.left_audiogram_symbol = {'symbol': 'x',
                                      'symbolPen': (0, 20, 255),
                                      'symbolBrush': (0, 20, 255),
                                      'symbolSize': 10}

        # Checkbone also modifies the pen, so we might as well set it up right now
        self.checkBone.stateChanged.connect(self.set_pens_and_symbols)
        self.checkBone.setChecked(False)

        # Plot setup
        self.plotWidget.setMenuEnabled(False)
        self.evoked_X_axis = np.linspace(0, self.cycle_duration, self.cycle_duration * SAMPLINGRATE // 1000)
        self.evoked_Y_range = (-PEAK_TO_PEAK_EVOKED // 2, PEAK_TO_PEAK_EVOKED // 2)
        self.nulldata = np.zeros_like(self.evoked_X_axis)
        self.plot_null()
        self.audiogram_figure_ready = False

        # Amplitude setup, initialize to midpoint
        self.amplitudes = CABRA_Window.valid_amplitudes
        self.id_min = 0
        self.id_max = len(self.amplitudes) - 1
        self.id_mid = self.amplitudes.index(0)  # 0 [dbHL]
        self.dbamp = self.amplitudes[self.id_mid]

        # Filepath to store the recording
        self.filepath = ''

        # Process communication setup
        self.process = QProcess(self)
        self.process_path = CABRA_Window.process_paths['CABRA device']
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
            QPushButton { background-color: rgb(131, 153, 105); color: rgb(0, 0, 0); }
        """)
        self.pushNOISE.setStyleSheet("""
            QPushButton:disabled { background-color: gray; }
            QPushButton { background-color: rgb(199, 122, 108); color: rgb(0, 0, 0); }
        """)

        # Initialize audiograms as nan arrays
        self.audiogram_left = np.ones(self.comboBoxFreq.count()) * np.nan
        self.audiogram_right = np.ones(self.comboBoxFreq.count()) * np.nan

        # Connect the CABRASweep button
        self.pushCABRASweep.clicked.connect(self.CABRASweep)
        self.pushCABRA_default_color = '''{background-color: rgb(230, 97, 0); 
                                          color: rgb(0, 0, 0); 
                                          font: Bold Italic 11pt "Arial Bold"; }'''
        self.pushCABRASweep.setStyleSheet("QPushButton:disabled { background-color: gray; }" + \
                                          f"QPushButton {self.pushCABRA_default_color}")

        # Connect process selection actions
        self.actionCABRA_Default.triggered.connect(lambda: self.change_process_path('CABRA device'))
        self.actionSimulator.triggered.connect(lambda: self.change_process_path('simulation'))

        # Bind Ctrl + C to abort_test
        self.abort_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.abort_shortcut.activated.connect(self.abort_test)

    def show_tone_burst_dialog(self):
        """
        Pop up a dialog to set up tone burst specifications
        """
        dialog = ToneBurstDialog()
        # Set the current values to the dialog
        dialog.spinClickDuration.setValue(self.click_duration)
        dialog.spinCycleDuration.setValue(self.cycle_duration)
        dialog.spinNClicks.setValue(self.n_clicks)
        dialog.accepted.connect(lambda: self.update_tone_burst_parameters(dialog))
        dialog.exec()

    def update_tone_burst_parameters(self, dialog):
        """
        Update the tone burst parameters based on the dialog
        """
        self.n_clicks = dialog.spinNClicks.value()
        self.click_duration = dialog.spinClickDuration.value()
        self.cycle_duration = dialog.spinCycleDuration.value()

    def set_pens_and_symbols(self):
        """
        Change the pen color for the evoked potential plot
        """
        if self.checkBone.isChecked():
            # Green for evoked, cyan for right ear, yellow for left ear
            self.evoked_pen = mkPen(color=(0, 255, 0), width=2)
            self.right_audiogram_pen = mkPen(color=(0, 255, 255), width=3)
            self.right_audiogram_symbol = {'symbol': 'o',
                                           'symbolPen': (0, 255, 255),
                                           'symbolBrush': (0, 255, 255),
                                           'symbolSize': 10}
            self.left_audiogram_pen = mkPen(color=(255, 255, 0), width=3)
            self.left_audiogram_symbol = {'symbol': 'x',
                                          'symbolPen': (255, 255, 0),
                                          'symbolBrush': (255, 255, 0),
                                          'symbolSize': 10}
        else:
            # Default colors: red for evoked, orange for right, blue for left
            self.evoked_pen = mkPen(color=(255, 0, 0), width=2)
            self.right_audiogram_pen = mkPen(color=(230, 97, 0), width=3)
            self.right_audiogram_symbol = {'symbol': 'o',
                                           'symbolPen': (230, 97, 0),
                                           'symbolBrush': (230, 97, 0),
                                           'symbolSize': 10}
            self.left_audiogram_pen = mkPen(color=(0, 20, 255), width=3)
            self.left_audiogram_symbol = {'symbol': 'x',
                                          'symbolPen': (0, 20, 255),
                                          'symbolBrush': (0, 20, 255),
                                          'symbolSize': 10}

    def change_process_path(self, mode):
        """
        Change the process path to the given mode
        """
        self.process_path = CABRA_Window.process_paths[mode]
        self.restart_process()
        self.labelStatus.setText(f"Mode changed to {mode}")
        if mode == 'simulation':
            self.actionSimulator.setChecked(True)
            self.actionCABRA_Default.setChecked(False)
            self.n_clicks = 50
            self.click_duration = 5
            self.cycle_duration = 10

    def update_run_button_to_stop(self):
        """
        Update the RUN button to act as a STOP button during recording.
        """
        self.pushRUN.setText("STOP")
        self.pushRUN.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.MediaPlaybackStop))
        self.pushRUN.clicked.disconnect()
        self.pushRUN.clicked.connect(self.abort_test)
        self.pushRUN.setStyleSheet(u"background-color: rgb(171, 143, 202);\n"
                                   "color: rgb(0,0,0);\n"
                                   "font: 700 11pt \"Arial\";")

    def reset_stop_button_to_run(self):
        """
        Reset the RUN button to its original state.
        """
        self.pushRUN.setText("REC")
        self.pushRUN.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.AudioInputMicrophone))
        self.pushRUN.clicked.disconnect()
        self.pushRUN.clicked.connect(self.on_click_pushRUN)
        self.pushRUN.setStyleSheet(u"background-color: rgb(246, 211, 45);\n"
                                   "color: rgb(0,0,0);\n"
                                   "font: 700 11pt \"Arial\";")

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
        nclicks = self.n_clicks
        click_duration = self.click_duration
        cycle_duration = self.cycle_duration
        return f"{Actions.RECORD} {nclicks} {freq_idx} {ear} {dbamp} {click_duration} {cycle_duration}\n"

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

    def restart_process(self):
        """
        Restart the process
        """
        self.process.kill()
        self.process.waitForFinished(500)

        # Start the process again
        self.start_process()
        self.labelStatus.setText(f"Restarted connection for {self.process_path}")
        self.audiogram_left = np.ones_like(self.audiogram_left) * np.nan
        self.audiogram_right = np.ones_like(self.audiogram_right) * np.nan

    def _print_msg(self):
        """
        Just for debugging purposes
        """
        print(self.get_msg())

    #@pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        # self.labelStatus.setText(data)
        if not data:
            return
        if '.npy' in data:
            filepath, n_reps = data.strip().split(';')
            self.filepath = filepath
            self.n_reps = int(n_reps)
            self.recording_completed.emit()
        else:
            self.handle_stderr()

    @pyqtSlot()
    def handle_stderr(self):
        output = self.process.readAllStandardError().data().decode()
        if not output:
            return
        # Connection error: popout window for user to check connection
        if output == '1':
            self.labelStatus.setText("Connection error occurred.")
            msg_box = DialogReconnect(self)
            msg_box.exec()

        elif output == '2':
            self.labelStatus.setText("Data transmission error. Please try again.")
            self.reset_stop_button_to_run()
            self.state = CABRA_Window.STATE_IDLE
            self.pushRUN.setEnabled(True)
        elif output == '3':
            self.labelStatus.setText("No repetition fit within the threshold. Please try again.")
        else:
            self.labelStatus.setText(f"Invalid message: {output}")

    @pyqtSlot()
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
        self.labelStatus.setText(f"Recording completed and stored at {self.filepath}, {self.n_reps} repetitions.")
        # Set pushNOISE and pushEVOKED to be enabled
        self.pushEVOKED.setEnabled(True)
        self.pushNOISE.setEnabled(True)
        # Plot
        self.plot_evoked()

    ##############################################################################################
    # The following methods are related to the audiometry test, and the audiogram plotting/saving #
    ##############################################################################################

    # Abort the current test and reset the state to idle using Ctrl + C
    def abort_test(self):
        """
        Abort the current test and reset the state to idle
        Also restart process
        """
        self.labelStatus.setText("Test aborted.")
        self.restart_process()
        self.pushCABRASweep.setEnabled(True)
        self.reset_stop_button_to_run()
        self.pushEVOKED.setEnabled(False)
        self.pushNOISE.setEnabled(False)
        self.reset_dbamp()
        self.state = CABRA_Window.STATE_IDLE
        self.plot_null()

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

    def set_axis_for_evoked(self):
        """
        Set labels, ranges and ticks for the evoked potential plot
        """
        self.plotWidget.plotItem.setTitle("")  # Clear the title
        self.plotWidget.plotItem.showGrid(x=False, y=False)  # Disable the grid
        self.plotWidget.setLabel('bottom', 'Time [ms]')
        self.plotWidget.setLabel('left', 'Amplitude [uv]')
        self.plotWidget.setYRange(self.evoked_Y_range[0], self.evoked_Y_range[1], padding=0.)
        # self.plotWidget.autoRange()
        self.plotWidget.setXRange(self.evoked_X_axis[0], self.evoked_X_axis[-1], padding=0.)

        ax = self.plotWidget.getAxis('bottom')
        ax.setTicks([[(i, str(i)) for i in range(int(self.evoked_X_axis[0]), int(self.evoked_X_axis[-1]) + 1)]])
        ax.setLabel('Time [ms]')
        ay = self.plotWidget.getAxis('left')
        ay.setTicks([[(i, str(i)) for i in range(self.evoked_Y_range[0], self.evoked_Y_range[1] + 1, 50)]])
        ay.setLabel('Amplitude [uv]')

        # Automatic ticks
        self.plotWidget.getAxis('bottom').setTicks(None)
        self.plotWidget.getAxis('left').setTicks(None)

        # Set a double grid
        self.plotWidget.plotItem.showGrid(x=True, y=True, alpha=0.1)  # Minor grid
        self.plotWidget.plotItem.showGrid(x=True, y=True, alpha=0.5)  # Major grid

    def plot_null(self):
        """
        Plot a null graph
        """
        # Reset the plotWidget by removing legends, ticks, axis labels, and all
        self.plotWidget.clear()
        self.plotWidget.plot(self.evoked_X_axis, self.nulldata, pen=self.evoked_pen)
        self.set_axis_for_evoked()

    def plot_evoked(self):
        """
        Plot the evoked potential
        """
        if self.filepath:
            evoked = np.load(self.filepath)
            self.plotWidget.clear()
            self.plotWidget.plot(self.evoked_X_axis, evoked, pen=self.evoked_pen)
            self.set_axis_for_evoked()
        else:
            self.plot_null()
            self.labelStatus.setText("No file to plot.")

    def plot_audiogram(self):
        """
        Plot the audiogram once it's finished. The 'save_audiogram' shoud be saved right after this function.
        """
        # Plotting
        self.plotWidget.clear()

        # Add legend at the bottom right
        self.plotWidget.plot(self.audiogram_left, pen=self.left_audiogram_pen, name='Left ear',
                             **self.left_audiogram_symbol)
        self.plotWidget.plot(self.audiogram_right, pen=self.right_audiogram_pen, name='Right ear',
                             **self.right_audiogram_symbol)
        self.plotWidget.setXRange(0, len(self.audiogram_left) - 1, padding=0.05)
        self.plotWidget.setYRange(-10, 100, padding=0.05)
        self.plotWidget.invertY(True)
        self.plotWidget.setTitle(f"Audiogram for {self.nameEdit.text()}")

        # Axis setup
        ax = self.plotWidget.getAxis('bottom')
        ax.setTicks([[(i, str(self.comboBoxFreq.itemText(i))) for i in range(len(self.audiogram_left))]])
        ax.setLabel('Frequency [Hz]')
        ay = self.plotWidget.getAxis('left')
        ay.setTicks([[(amp, str(amp)) for amp in range(-10, 110, 10)]])
        ay.setLabel('Amplitude [dB HL]')

        # Legend at the BOTTOM RIGHT
        legend = self.plotWidget.plotItem.addLegend()
        legend.anchor((1, 1), (1, 1))
        legend.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        legend.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))

        # Update the audiogram's saved status
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
        self.id_mid = self.amplitudes.index(0)
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
            self.update_run_button_to_stop()
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
        else:
            self.reset_stop_button_to_run()
            self.state = CABRA_Window.STATE_IDLE

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
            for widget in [self.pushCABRASweep, self.nameEdit, self.dateEdit, self.lineID]:
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
        for widget in [self.pushCABRASweep, self.nameEdit, self.dateEdit, self.lineID]:
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
        self.process.write(f"{Actions.EXIT}\n".encode())
        self.process.waitForBytesWritten()
        self.process.terminate()
        event.accept()


class DialogReconnect(Ui_DialogReconnect, QDialog):
    def __init__(self, parent: CABRA_Window):
        self.parent = parent
        super().__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.on_reject)

    def on_accept(self):
        self.parent.restart_process()
        self.close()

    def on_reject(self):
        self.parent.actionSimulator.trigger()
        self.parent.restart_process()
        self.close()


class ToneBurstDialog(Ui_DialogToneBurst, QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Update maximum click duration based on cycle duration
        self.spinCycleDuration.valueChanged.connect(self.change_max_click_duration)
        self.change_max_click_duration()

    def change_max_click_duration(self):
        """
        Click duration must be smaller that cycle duration
        Modify the minimum value of the click duration spinbox accordingly
        """
        self.spinClickDuration.setMaximum(self.spinCycleDuration.value())


def run_ui():
    app = QApplication(sys.argv)
    window = CABRA_Window()
    window.show()
    app.exec()


if __name__ == '__main__':
    run_ui()
