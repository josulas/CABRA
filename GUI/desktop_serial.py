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
BAUDRATE = 960_000  # (MUST BE THE SAME AS IN THE ESP32 CODE)
NUMBER_OF_BAUDS_PER_BIT = 10 # (DO NOT CHANGE)
SAMPLINGRATE = 12_000 # Hz (MUST BE THE SAME AS IN THE ESP32 CODE)
BYTESPERSAMPLE = 2 # (DO NOT CHANGE)
NSAMPLESPERBUFFER = 128 # (MUST BE THE SAME AS IN THE ESP32 CODE)
MAXNSAMPLES = 2_000 # (MUST BE THE SAME AS IN THE ESP32 CODE)
ADCRESOLUTION = 12 # bits (DO NOT CHANGE)
QUANTIZATION = 2 ** ADCRESOLUTION
ADCMAX = 3.1  # V
ADCMIN = 0.15 # V
ADCRANGE = ADCMAX - ADCMIN
THRESHOLDV = 40 #e-6
GAIN = 50 * 390 / (8 / 3.1)
THRESHOLD = THRESHOLDV * GAIN /  ADCRANGE * QUANTIZATION
OUTPUT_DIR = 'saved_data'
SERIAL_RECOGNIZER = "USB to UART Bridge"

# Player parameters
# Path to the C executable
PLAYER_PATH_WINDOWS = r"./audio_playback_windows/audio_playback.exe"
PLAYER_PATH_LINUX = r"./audio_playback_linux/audio_playback"
TEMP_WAV_FILE = "~.wav"


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
                 alpha_s: int = 40,
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
        self.freq_index = None
        self.ear = None
        self.click_dbamp = None
        self.click_duration = None
        self.cycle_duration = None
        self.nsamples_per_click = None
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
            raise OSError("Unsupported platform")

    def _init_filter(self) -> np.ndarray:
        """
        Initialize the filter design
        :return: IIR filter coefficients
        """
        bandpass_iir = signal.iirdesign([self.f_pass, self.f_stop],
                                        [self.f_pass - self.delta_f, self.f_stop + self.delta_f],
                                        gpass=1, gstop = self.alpha_s,
                                        fs=self.sampling_rate,
                                        output='sos')
        return bandpass_iir
    
    def set_serial(self, nclicks: int, freq_idx: int, ear: int, click_dbamp: int, click_duration: int, cycle_duration: int):
        if self.port is not None:
            self.nclicks = nclicks
            self.freq_index = freq_idx
            self.ear = ear
            self.click_dbamp = click_dbamp
            self.click_duration = click_duration
            self.cycle_duration = cycle_duration
            self.nsamples_per_click = int(np.ceil(cycle_duration * SAMPLINGRATE / 1000.0))
            if self.nsamples_per_click > MAXNSAMPLES:
                raise ValueError(F"Number of samples per click should be less than {MAXNSAMPLES}, got {self.nsamples_per_click} instead.")
            self.waitingtime = self.nsamples_per_click / SAMPLINGRATE + self.nsamples_per_click * BYTESPERSAMPLE * 8 * NUMBER_OF_BAUDS_PER_BIT / self.baudrate + 0.5
            try:
                self.serial = Serial(self.port, self.baudrate, timeout=self.waitingtime)
                # self.serial = Serial(self.port, self.baudrate, timeout=None)
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

        max_transmission_errors = int(self.nclicks * .05)
        transmission_errors = 0
        self.clicker.saveToneBurst(TEMP_WAV_FILE)
        send_command(self.player, TEMP_WAV_FILE, "U")
        send_command(self.player, "L", "D")
        self.serial.read(self.serial.inWaiting())
        data = []
        for _ in range(self.nclicks):
            self.serial.write(f"{self.nsamples_per_click}".encode())
            send_command(self.player, "P", "S")
            self.serial.write("S".encode())
            try:
                binary_data = self.serial.read(self.nsamples_per_click * 2)
            except serial.serialutil.SerialException:
                raise ConnectionError("Serial connection lost")
            if len(binary_data) != self.nsamples_per_click * 2:
                transmission_errors += 1
                if transmission_errors > max_transmission_errors:
                    raise RuntimeError(F"Serial read timed out before receiving all data. Expected {self.nsamples_per_click} bytes, got {len(binary_data)} bytes.")
            else:
                data.append(np.frombuffer(binary_data, dtype=np.uint16).astype(np.float64))
            time.sleep(0.012) # Avoids glitches in the clicks
        data = np.array(data)
        if len(data):
            data = signal.sosfiltfilt(self.bandpass_iir, data, axis=1)
            self.data =  data[(data.max(axis=1) - data.min(axis=1)) <= self.threshold]
        else:
            self.data = data

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

    def get_data_average(self, mode: str='homogenous'):
        """
        Get the average of the recorded data
        :param mode: mode for the average
        :return: averaged data
        """
        if self.data is None or len(self.data) == 0:
            raise RuntimeError("No data recorded")
        averaged_data = average_EEG(self.data, mode=mode)
        self.averaged_data = averaged_data * ADCRANGE / (QUANTIZATION * GAIN) * 1e9 # nV

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
        sys.stderr.write('9')
        sys.stderr.flush()
        return None, None
    except KeyboardInterrupt:
        return Actions.EXIT, None
    except IndexError:
        sys.stderr.write('9')
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
                                  cycle_duration=click_duration,
                                  nclicks=1,
                                  samplingrate=48_000)
                laptop_serial.set_clicker(clicker)
                try:
                    laptop_serial.set_serial(nclicks, freq_index, ear, click_dbamp, click_duration, cycle_duration)
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
                try:
                    laptop_serial.get_data_average()
                except RuntimeError:
                    sys.stderr.write('3')
                    sys.stderr.flush()
                    continue
                f_name = f'{frequency}Hz_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.npy'
                f_path = os.path.join(OUTPUT_DIR, f_name)
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                laptop_serial.save_averaged_data(f_path)
                sys.stdout.write(f"{f_path};{laptop_serial.data.shape[0]}")
                sys.stdout.flush()
            case Actions.RESET:
                pass
            case Actions.EXIT:
                stop = True

if __name__ == '__main__':
    main()
