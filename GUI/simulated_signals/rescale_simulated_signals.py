import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import resample

SAMPLINGRATE = 12_000
SCALE_FACTOR = 1.
TIME_LEN = 30 # ms


def rescale_sim_signals():
    # Load the simulated signals
    fname = 'noise.npy'
    simulated_signals = np.load(fname)

    # Rescale the simulated signals
    rescaled_signals = simulated_signals * SCALE_FACTOR

    # Resample the signals
    rescaled_signals = resample(rescaled_signals, int(TIME_LEN * SAMPLINGRATE / 1_000))
    plt.plot(rescaled_signals)
    plt.title(f'Rescaled and resampled signals. Len = {len(rescaled_signals)}')
    plt.show()
    # Save the rescaled signals
    confirm = input('Do you want to save the rescaled signals? [y/n]: ')
    if confirm.lower() == 'y':
        np.save(fname, rescaled_signals)
        print('Rescaled and resampled the simulated signals')


if __name__ == '__main__':
    rescale_sim_signals()
