import time
from serial import Serial
import serial.tools.list_ports
import numpy as np
import scipy.signal as signal
import RPi.GPIO as GPIO
from average_eeg import average_EEG
from playaudio import Clicker, EarSelect
from datetime import datetime
import sys
import os

# Board parameters
STANDARD_FREQUENCIES_DICT = {0: 250, 1: 500, 2: 1000, 3: 2000, 4: 4000, 5: 8000}
BAUDRATE = 960000  # (DO NOT CHANGE)
SAMPLINGRATE = 10000 # Hz (DO NOT CHANGE)
BYTESPERSAMPLE = 2 # (DO NOT CHANGE)
BUFFERSIZE = 128 # (DO NOT CHANGE)
EEGRANGE = 5e-6 # Vpp
SIGNALRANGE = 1 # Vpp
ADCRESOLUTION = 12 # bits (DO NOT CHANGE)
QUANTIZATION = 2 ** ADCRESOLUTION
ADCMAX = 3.3 # V
ADCMIN = 0.15 # V
ADCRANGE = ADCMAX - ADCMIN
THRESHOLDV = 40e-6
GAIN = 30000 / 4 # SIGNALRANGE / EEGRANGE
THRESHOLD = THRESHOLDV * GAIN /  ADCRANGE * QUANTIZATION
INTERRUPTION_PIN = 11
RESET_ESP_PIN = 12
OUTPUT_DIR = 'saved_data'
SERIAL_RECOGNIZER = "USB to UART Bridge Controller"


class Actions:
    RECORD = 0
    RESET = 1
    EXIT = 2
    def __iter__(self):
        yield Actions.RECORD
        yield Actions.RESET
        yield Actions.EXIT


class ESPSerial:
    def __init__(self,
                 clicker: Clicker | None = None,
                 port: str | None = None,
                 baudrate: int = BAUDRATE,
                 sampling_rate: int = SAMPLINGRATE,
                 buffersize: int = SAMPLINGRATE,
                 bytessample: int = BYTESPERSAMPLE,
                 alpha_s: int = 45,
                 delta_f: int = 10,
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
            try:
                port = self._find_port()
            except serial.serialutil.SerialException:
                pass
        self.port = port
        self.baudrate = baudrate
        self.sampling_rate = sampling_rate
        self.buffersize = buffersize
        self.bytessample = bytessample
        self.nclicks = None
        self.nsamples = None
        self.nbytes = None
        self.nusefulsamples = None
        self.clicknumberofsamples = None
        self.waitingtime = None
        self.serial = None

        # Filter design
        self.alpha_s = alpha_s
        self.delta_f = delta_f
        self.f_pass = f_pass
        self.f_stop = f_stop
        self.bandpass_iir = self._init_filter()

        # Data acquisition
        self.threshold = amplitude_threshold
        self.data = None
        self.averaged_data = None

        # setup GPIO pins
        self._setup_gpio_pins()
    
    @staticmethod
    def _setup_gpio_pins():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INTERRUPTION_PIN, GPIO.OUT)
        GPIO.output(INTERRUPTION_PIN, GPIO.LOW)
        GPIO.setup(RESET_ESP_PIN, GPIO.OUT)
        GPIO.output(RESET_ESP_PIN, GPIO.LOW)

    @staticmethod
    def reset_esp():
        GPIO.output(RESET_ESP_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RESET_ESP_PIN, GPIO.LOW)
    
    @staticmethod
    def close_gpio_pins():
        GPIO.cleanup()

    @staticmethod
    def _find_port() -> str:
        """
        Automatically detect USB for the ESP32
        :return:
        """
        ports = serial.tools.list_ports.comports()
        for port, desc, _ in sorted(ports):
            if SERIAL_RECOGNIZER in desc:
                return port
        raise serial.serialutil.SerialException('ESP not found')

    def _init_filter(self) -> np.ndarray:
        """
        Initialize the filter design
        :return: IIR filter coefficients
        """
        bandpass_iir = signal.iirdesign([self.f_pass, self.f_stop],
                                        [self.f_pass - self.delta_f, self.f_stop + self.delta_f],
                                        .2,
                                        self.alpha_s,
                                        fs=self.sampling_rate,
                                        output='sos')
        return bandpass_iir
    
    def set_serial(self, nclicks: int, cycle_duration: int):
        if self.port is not None:
            self.nclicks = nclicks
            self.nsamples = int(np.ceil(nclicks * cycle_duration/ 1000.0 * SAMPLINGRATE / BUFFERSIZE)) * BUFFERSIZE 
            self.nbytes = self.nsamples * BYTESPERSAMPLE
            self.nusefulsamples = int(nclicks * cycle_duration / 1000.0 * SAMPLINGRATE)
            self.clicknumberofsamples = int(cycle_duration / 1000.0 * SAMPLINGRATE)
            self.waitingtime = cycle_duration / 1000.0 * nclicks + 5
            self.serial = Serial(self.port, self.baudrate, timeout=None)
            # self.serial = Serial(self.port, self.baudrate, timeout=self.waitingtime)

    def record_data(self):
        """
        Record data from the ESP32
        :return: numpy array with the recorded data
        """
        if self.serial is None:
            raise RuntimeError("Serial connection not initialized")
        if self.clicker is None:
            raise RuntimeError("Clicker object was not set")

        self.serial.read(self.serial.inWaiting())
        self.serial.write(f"{self.nusefulsamples}".encode())
        self.clicker.playToneBurst(False)
        GPIO.output(INTERRUPTION_PIN, GPIO.HIGH)
        binary_data = self.serial.read(self.nbytes)
        print(self.serial.inWaiting())
        GPIO.output(INTERRUPTION_PIN, GPIO.LOW)
        if len(binary_data) != self.nbytes:
            raise RuntimeError(F"Serial read timed out before receiving all data. Expected {self.nbytes} bytes, got {len(binary_data)} bytes.")
        data = np.frombuffer(binary_data, dtype=np.uint16)[:self.nusefulsamples]
        data = data.reshape((self.nclicks, self.clicknumberofsamples)).astype(np.float64)
        data = signal.sosfiltfilt(self.bandpass_iir, data, axis=1)
        useful_data = data[(data.max(axis=1) - data.min(axis=1)) <= self.threshold]
        self.data = useful_data

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

    def get_data_average(self, mode: str='both'):
        """
        Get the average of the recorded data
        :param mode: mode for the average
        :return: averaged data
        """
        if self.data is None:
            raise RuntimeError("No data recorded")
        averaged_data = average_EEG(self.data, mode=mode)
        self.averaged_data = averaged_data

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


def manage_input():
    """
    Data receiving operation
    arg0: action
    if arg0 == Actions.RECORD:
        arg1: nclicks
        arg2: freq_index
        arg3: ear
        arg4: click_dbamp    (db)
        arg5: click_duration (ms)
        arg6: cycle_duration (ms)
    """
    try:
        control = sys.stdin.readline().split()
        action = int(control[0])
        if action not in list(Actions()):
            raise ValueError(F"Action should be one of {list(Actions())}, got {action} instead.")
        if action == Actions.RECORD:
            nclicks = int(control[1])
            if nclicks < 1:
                raise ValueError(F"Number of clicks should be greater than 1, got {nclicks} instead.")
            freq_index = int(control[2])
            if freq_index not in STANDARD_FREQUENCIES_DICT:
                raise ValueError(F"Frequency index should be one of {list(STANDARD_FREQUENCIES_DICT.keys())}, got {freq_index} instead.")
            ear = int(control[3])
            if ear not in list(EarSelect()):
                raise ValueError(F"Ear should be one of {list(EarSelect())}, got {ear} instead.")
            click_dbamp = int(control[4])
            if not -10 <= click_dbamp <= 40:
                raise ValueError(F"Click amplitude should be between -10 and 40 dB, got {click_dbamp} instead.")
            click_duration = int(control[5])
            if click_duration < 1:
                raise ValueError(F"Click duration should be greater than 1, got {click_duration} instead.")
            cycle_duration = int(control[6])
            if cycle_duration < click_duration:
                raise ValueError(F"Cycle duration should be greater than click duration, got {cycle_duration} instead.")
            return action, [nclicks, freq_index, ear, click_dbamp, click_duration, cycle_duration]
        else:
            return action, None
    except ValueError:
        sys.stderr.write('3')
        sys.stderr.flush()
        return None, None
    except KeyboardInterrupt:
        return Actions.EXIT, None
    except IndexError:
        sys.stderr.write('3')
        sys.stderr.flush()
        return None, None


def main():
    # PIN SETUP
    rpiserial = ESPSerial()
    if rpiserial.port is None:
        sys.stderr.write('1')
        sys.stderr.flush()
        stop = True
    stop = False
    while not stop:
        action, params = manage_input()
        match action:
            case Actions.RECORD:
                nclicks, freq_index, ear, click_dbamp, click_duration, cycle_duration = params
                frequency = STANDARD_FREQUENCIES_DICT[freq_index]
                clicker = Clicker(freq=frequency,
                                  ear=ear,
                                  dbamp=click_dbamp,
                                  click_duration=click_duration,
                                  cycle_duration=cycle_duration,
                                  nclicks=nclicks)
                rpiserial.set_clicker(clicker)
                rpiserial.set_serial(nclicks, cycle_duration)
                try:
                    rpiserial.record_data()
                except Exception as e:
                    sys.stderr.write('2')
                    sys.stderr.flush()
                    continue
                rpiserial.close()
                rpiserial.get_data_average()
                f_name = f'{frequency}Hz_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
                rpiserial.save_averaged_data(os.path.join(OUTPUT_DIR, f_name))
                sys.stdout.write(f_name)
                sys.stdout.flush()
            case Actions.RESET:
                rpiserial.reset_esp()
            case Actions.EXIT:
                stop = True
    rpiserial.close_gpio_pins()

if __name__ == '__main__':
    main()
