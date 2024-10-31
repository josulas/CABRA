import time
from serial import Serial
import serial.tools.list_ports
import numpy as np
import scipy.signal as signal
import RPi.GPIO as GPIO
from average_eeg import average_EEG
from playaudio import Clicker
from datetime import datetime

# Board parameters
BAUDRATE = 960000
NCLICKS = 500
CYCLEDURATION = 30 # ms (including pause)
CLICKDURATION = 10 #ms
SAMPLINGRATE = 10000 # Hz
BYTESPERSAMPLE = 2
BUFFERSIZE = 128
EEGRANGE = 5e-6 # Vpp
SIGNALRANGE = 1 # Vpp
ADCRESOLUTION = 12 # bits
QUANTIZATION = 2**ADCRESOLUTION
ADCMAX = 3.3 # V
ADCMIN = 0.15 # V
ADCRANGE = ADCMAX - ADCMIN
THRESHOLDV = 40e-6
GAIN = 30000 / 4 # SIGNALRANGE / EEGRANGE
THRESHOLD = THRESHOLDV * GAIN /  ADCRANGE * QUANTIZATION
INTERRUPTION_PIN = 11

# PIN SETUP
GPIO.setmode(GPIO.BOARD)
GPIO.setup(INTERRUPTION_PIN, GPIO.OUT)
GPIO.output(INTERRUPTION_PIN, GPIO.LOW)

class RPISerial:
    def __init__(self,
                 clicker: Clicker = None,
                 port: str | None = None,
                 baudrate: int = BAUDRATE,
                 sampling_rate: int = SAMPLINGRATE,
                 buffersize: int = SAMPLINGRATE,
                 bytessample: int = BYTESPERSAMPLE,
                 frequencies: dict[int, int] = {0: 250, 1: 500, 2: 1000, 3: 2000, 4: 4000, 5: 8000},
                 alpha_s: int = 45,
                 DeltaF: int = 10,
                 f_pass: int = 150,
                 f_stop: int = 3000,
                 amplitude_threshold: float = THRESHOLD):
        """
        Initializes the serial connection with the ESP32
        :param port: USB port where the ESP32 is connected. Can be found automatically if None
        :param baudrate: Baud rate for the serial connection
        :param sampling_rate: Sampling frequency for the ESP
        :param buffersize: Samples per buffer
        :param bytessample: Bytes per sample
        """
        self.clicker = clicker

        # Serial connection
        if port is None:
            port = self._find_port()
        self.port = port
        self.baudrate = baudrate
        self.sampling_rate = sampling_rate
        self.buffersize = buffersize
        self.bytessample = bytessample
        self.serial = Serial(port, baudrate, timeout=None)
        time.sleep(2)  # Allow time for connection to establish

        # Calculated parameters
        self.nbytes = int(np.ceil(NCLICKS * CYCLEDURATION / 1000.0 * SAMPLINGRATE / BUFFERSIZE)) * BUFFERSIZE * BYTESPERSAMPLE
        self.nusefulsamples = int(NCLICKS * CYCLEDURATION / 1000.0 * SAMPLINGRATE)
        self.clicknumberofsamples = int(CYCLEDURATION / 1000.0 * SAMPLINGRATE)
        self.xvals = np.arange(0, self.clicknumberofsamples, 1) * CYCLEDURATION / self.clicknumberofsamples # ms
        self.waitingtime = CYCLEDURATION / 1000.0 * NCLICKS

        # Filter design
        self.frequencies = frequencies
        self.alpha_s = alpha_s
        self.DeltaF = DeltaF
        self.f_pass = f_pass
        self.f_stop = f_stop
        self.bandpass_iir = self._init_filter()

        # Data acquisition
        self.threshold = amplitude_threshold
        self.data = None
        self.averaged_data = None

    @staticmethod
    def _find_port() -> str:
        """
        Automatically detect USB for the ESP32
        :return:
        """
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            if 'tty' in desc:
                return port

    def _init_filter(self) -> np.ndarray:
        """
        Initialize the filter design
        :return: IIR filter coefficients
        """
        bandpass_iir = signal.iirdesign([self.f_pass, self.f_stop],
                                        [self.f_pass - self.DeltaF, self.f_stop + self.DeltaF],
                                        .2,
                                        self.alpha_s,
                                        fs=self.sampling_rate,
                                        output='sos')
        return bandpass_iir

    def record_data(self) -> np.ndarray:
        """
        Record data from the ESP32
        :return: numpy array with the recorded data
        """
        assert self.clicker is not None, "Clicker not set"

        self.clicker.playToneBurst(False)
        GPIO.output(INTERRUPTION_PIN, GPIO.HIGH)
        binary_data = self.serial.read(self.nbytes)
        GPIO.output(INTERRUPTION_PIN, GPIO.LOW)
        data = np.frombuffer(binary_data, dtype=np.uint16)[:self.nusefulsamples]
        data = data.reshape((NCLICKS, int(CYCLEDURATION / 1000 * SAMPLINGRATE))).astype(np.float64)
        data = signal.sosfiltfilt(self.bandpass_iir, data, axis=1)
        useful_data = data[(data.max(axis=1) - data.min(axis=1)) <= self.threshold]

        self.data = useful_data
        return useful_data

    def close(self):
        """
        Close the serial connection
        """
        self.serial.close()

    def set_clicker(self, clicker: Clicker):
        """
        Set the clicker
        :param clicker: new clicker
        """
        self.clicker = clicker

    def get_data_average(self, mode: str='homogenous') -> np.ndarray:
        """
        Get the average of the recorded data
        :param mode: mode for the average
        :return: averaged data
        """
        assert self.data is not None, "No data recorded"
        averaged_data = average_EEG(self.data, mode=mode)
        self.averaged_data = averaged_data
        return averaged_data

    def save_raw_data(self, filename: str):
        """
        Save the recorded data to a file
        :param filename: name of the file
        """
        np.save(filename, self.data)

    def save_averaged_data(self, filename: str):
        """
        Save the averaged data to a file
        :param filename: name of the file
        """
        np.save(filename, self.averaged_data)


def main():
    try:
        rpiserial = RPISerial()
        while True:
            # Select freq. stimulus
            print('Available frequencies:', rpiserial.frequencies)
            option = input(f"Choose a frequency index (digit between 0 and {len(rpiserial.frequencies)}): ")
            while len(option) != 1 or not option.isdigit() or int(option) < 0 or int(option) > len(rpiserial.frequencies):
                print(f"Invalid input ({option}). Please enter a digit between 0 and {len(rpiserial.frequencies)}.")
                option = input(f"Choose a frequency index (digit between 0 and {len(rpiserial.frequencies)}): ")

            frequency = rpiserial.frequencies[int(option)]
            clicker = Clicker(freq=frequency, click_duration=CLICKDURATION, cycle_duration=CYCLEDURATION, nclicks=NCLICKS)
            rpiserial.set_clicker(clicker)

            # Extract data and take average
            data = rpiserial.record_data()
            print("Number of useful clicks: ", data.shape[0])
            evoked_potential = rpiserial.get_data_average()

            # Save data
            f_name = f'{frequency}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
            np.save(f_name, evoked_potential)
            print("Data saved to evoked_test.npy")

    except KeyboardInterrupt:
        print("\nExiting the program.\n")
    finally:
        if 'rpiserial' in locals():
            rpiserial.close()
        GPIO.cleanup()


if __name__ == '__main__':
    main()
