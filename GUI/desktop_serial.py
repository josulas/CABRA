import time
from datetime import datetime
import sys
import os
import subprocess
from serial import Serial
import serial.tools.list_ports
import numpy as np
import scipy.signal as signal
from average_eeg import average_EEG
from clicker import Clicker, EarSelect


# Board parameters
STANDARD_FREQUENCIES_DICT = {0: 250, 1: 500, 2: 1000, 3: 2000, 4: 4000, 5: 8000}
BAUDRATE = 960_000  # (DO NOT CHANGE)
SAMPLINGRATE = 8_000 # Hz (DO NOT CHANGE)
BYTESPERSAMPLE = 2 # (DO NOT CHANGE)
NSAMPLESPERBUFFER = 256 # (DO NOT CHANGE)
EEGRANGE = 5e-6 # Vpp
SIGNALRANGE = 1 # Vpp
ADCRESOLUTION = 12 # bits (DO NOT CHANGE)
QUANTIZATION = 2 ** ADCRESOLUTION
ADCMAX = 3.3  # V
ADCMIN = 0.15 # V
ADCRANGE = ADCMAX - ADCMIN
THRESHOLDV = 40e-6
GAIN = 50 * 390 / 3 # SIGNALRANGE / EEGRANGE
THRESHOLD = THRESHOLDV * GAIN /  ADCRANGE * QUANTIZATION
INTERRUPTION_PIN = 11
RESET_ESP_PIN = 12
OUTPUT_DIR = 'saved_data'
# SERIAL_RECOGNIZER = "USB to UART Bridge"
SERIAL_RECOGNIZER = "Bluetooth"

# Player parameters
# Path to the C executable
PLAYER_PATH_WINDOWS = "audio_playback.exe"
PLAYER_PATH_LINUX = "./audio_playback_linux"
TEMP_FILE = "~.wav"


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

        # Audio player
        self.player = self._init_player()

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
    
    def _init_player(self):
        platform_name = sys.platform
        if platform_name == 'win32':
            return subprocess.Popen([PLAYER_PATH_WINDOWS], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE, text=True)
        elif platform_name == 'linux':
            return subprocess.Popen([PLAYER_PATH_LINUX], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
        else:
            raise OSError(F"Platform {platform_name} not supported")

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
            self.nsamples = int(np.ceil(nclicks * cycle_duration/ 1000.0 * SAMPLINGRATE / NSAMPLESPERBUFFER
        )) * NSAMPLESPERBUFFER
         
            self.nbytes = self.nsamples * BYTESPERSAMPLE
            self.nusefulsamples = int(nclicks * cycle_duration / 1000.0 * SAMPLINGRATE)
            self.clicknumberofsamples = int(cycle_duration / 1000.0 * SAMPLINGRATE)
            self.waitingtime = cycle_duration / 1000.0 * nclicks + 1
            # self.serial = Serial(self.port, self.baudrate, timeout=None)
            try:
                self.serial = Serial(self.port, self.baudrate, timeout=self.waitingtime)
            except serial.serialutil.SerialException:
                raise ConnectionError("Serial connection lost")


    def record_data(self):
        """
        Record data from the ESP32
        :return: numpy array with the recorded data
        """
        def send_command(process, command, expected_response):
            process.stdin.write(command + "\n")
            process.stdin.flush()
            response = process.stdout.readline().strip()
            if response == expected_response:
                return True
            else:
                return False
        
        if self.serial is None:
            raise RuntimeError("Serial connection not initialized")
        if self.clicker is None:
            raise RuntimeError("Clicker object was not set")

        self.serial.read(self.serial.inWaiting())
        self.serial.write(f"{self.nusefulsamples}".encode())
        time.sleep(1)
        self.clicker.saveToneBurst(TEMP_FILE)
        send_command(self.player, TEMP_FILE, "U")
        send_command(self.player, "L", "D")
        send_command(self.player, "S", "F")
        self.serial.write("S".encode())
        try:
            binary_data = self.serial.read(self.nbytes)
        except serial.serialutil.SerialException:
            raise ConnectionError("Serial connection lost")
        finally:
            os.remove(TEMP_FILE)
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
        if self.data is None or len(self.data) == 0:
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
    stop = False
    laptop_serial = ESPSerial()
    if laptop_serial.port is None:
        sys.stderr.write('1')
        sys.stderr.flush()
        stop = True
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
                laptop_serial.set_clicker(clicker)
                try:
                    laptop_serial.set_serial(nclicks, cycle_duration)
                    laptop_serial.record_data()
                except RuntimeError:
                    sys.stderr.write('2')
                    sys.stderr.flush()
                    continue
                except ConnectionError:
                    sys.stderr.write('1')
                    sys.stderr.flush()
                    stop = True
                    break
                except KeyboardInterrupt:
                    stop = True
                    break
                laptop_serial.close()
                laptop_serial.get_data_average()
                f_name = f'{frequency}Hz_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.npy'
                f_path = os.path.join(OUTPUT_DIR, f_name)
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                laptop_serial.save_averaged_data(f_path)
                sys.stdout.write(f_path)
                sys.stdout.flush()
            case Actions.RESET:
                pass
            case Actions.EXIT:
                stop = True

if __name__ == '__main__':
    main()
