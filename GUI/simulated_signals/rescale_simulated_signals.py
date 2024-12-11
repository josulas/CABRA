import numpy as np

def rescale_sim_signals():
    # Load the simulated signals
    simulated_signals = np.load('evoked.npy')

    # Rescale the simulated signals
    rescaled_signals = simulated_signals * 4

    # Save the rescaled signals
    np.save('evoked.npy', rescaled_signals)

    print('Rescaled the simulated signals by a factor of 4')

if __name__ == '__main__':
    rescale_sim_signals()