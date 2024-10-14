import time
from serial import Serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal


# Board parameters
BAUDRATE = 500000
NCLICKS = 2000
CLICKDURATION = 30 # ms (including pause)
SAMPLINGRATE = 10000 # Hz
BYTESPERSAMPLE = 2
BUFFERSIZE = 2048
EEGRANGE = 5e-6 # Vpp
SIGNALRANGE = 1 # Vpp
ADCRESOLUTION = 12 # bits
QUANTIZATION = 2**ADCRESOLUTION
ADCMAX = 3.3 # V
ADCMIN = 0.15 # V
ADCRANGE = ADCMAX - ADCMIN
THRESHOLDV = 40e-6
GAIN = 22000 / 4 # SIGNALRANGE / EEGRANGE
THRESHOLD = THRESHOLDV * GAIN /  ADCRANGE * QUANTIZATION

# Functions
def average_EEG(X: np.ndarray, mode: str='homgenous') -> np.ndarray:
    """
    Performs a weighted or unweighted average of series of ERP EEG signals

    Args:
        X (np.ndarray): NxM matrix where every row is a new experiment and every column is a new sample
        mode (str, optional): Indicates how to perform the average. Could be:
            - homogenous: simple, unweighted average
            - amp: weight by amplitude
            - var: weight by variance
            - both: weight by both amplitude and variance
        Defaults to 'homogenous'.

    Returns:
        np.ndarray: an Mx1 array with the averaged signals
    """
    VALID_MODE = {'homogenous', 'amp', 'var', 'both'}
    if mode not in {'homogenous', 'amp', 'var', 'both'}:
        raise ValueError(F"{mode} is not a valid mode. Should be: {''.join(VALID_MODE)}")

    elif mode == 'homogenous':
        return np.mean(X, axis=0)
    
    # Find amplitudes
    s = np.mean(X, axis = 0)
    a = X.dot(s.T)

    # Find variances
    M = X.shape[1]
    V = np.var(X[:, -int(0.4*M):], axis=1)

    # Get weights and average
    if mode == 'amp':
        w = a / np.sum(a**2)
    elif mode == 'var':
        w = (1/V) / (np.sum(1/V))
    elif mode == 'both':
        w = (a/V) / (np.sum(a**2/V))
    
    return w.T.dot(X/np.sum(w))

# calculate the number of bytes to receive
nBytes = int(np.ceil(NCLICKS * CLICKDURATION / 1000.0 * SAMPLINGRATE / BUFFERSIZE)) * BUFFERSIZE * BYTESPERSAMPLE
nUsefulSamples = int(NCLICKS * CLICKDURATION / 1000.0 * SAMPLINGRATE)
clickNumberOfSamples = int(CLICKDURATION / 1000.0 * SAMPLINGRATE)
xvals = np.arange(0, clickNumberOfSamples, 1) * CLICKDURATION / clickNumberOfSamples # ms
waitingTime = CLICKDURATION / 1000.0 * NCLICKS
# Search for the appropriate port via bluetooth
connectionPort = None
ports = serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    if "Standard Serial over Bluetooth link" in desc:
        connectionPort = port
        break
if connectionPort is None:
    raise RuntimeError("No Bluetooth connection found")

# FILTER DESIGN
# Definición de parámetros
alpha_s = 45  # atenuación en dB de la banda de rechazo
DeltaF = 10  # Ancho de la ventana
bandpass_iir = signal.iirdesign([150, 3000], [150 - DeltaF, 3000 + DeltaF], .2, alpha_s, fs=SAMPLINGRATE, output='sos')


# Initialize the serial connection
ser = Serial(connectionPort, BAUDRATE, timeout=None)
time.sleep(2)  # Allow time for connection to establish
try:
    while True:
        # Sending data to ESP32
        message = input("Enter a command to send (digit between 0 and 5): ")
        while len(message) != 1 or not message.isdigit() or int(message) < 0 or int(message) > 5:
            print("Invalid input. Please enter a digit between 0 and 5.")
            message = input("Enter a command to send (digit between 0 and 5): ")
        ser.write(message.encode('utf-8'))  # Send the message
        # ser.close()
        # time.sleep(waitingTime)
        # try:
        #     ser.open()
        # except Exception as e:
        #     print("Error opening the serial port: ", e)
        #     exit(1)
        binaryData = ser.read(nBytes)
        # convert the binary data to a numpy array. Remember we have an uint16 each 2 bytes
        data = np.frombuffer(binaryData, dtype=np.uint16)[:nUsefulSamples]
        # Reshape the data. We have NCLICKS clicks, each one with CLICKDURATION ms / 1000 * SAMPLINGRATE samples
        data = data.reshape((NCLICKS, int(CLICKDURATION / 1000 * SAMPLINGRATE))).astype(np.float64)
        # Filter each click
        for repetition in range(NCLICKS):
            data[repetition] = signal.sosfilt(bandpass_iir, data[repetition])
        # Thresholding
        useful_data = data[(data.max(axis=1) - data.min(axis=1)) <= THRESHOLD]
        # Print the number of useful clicks
        print("Number of useful clicks: ", useful_data.shape[0])
        # get the evoked potential using an smart average
        evoked_potential = average_EEG(useful_data, mode='both')
        # plot the data and wait for the user to close the plot
        plt.plot(xvals, evoked_potential)
        plt.show()
            
except KeyboardInterrupt:
    print("\nExiting the program.\n")
finally:
    ser.close()  # Close the serial connection when done
