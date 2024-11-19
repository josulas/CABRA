import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':
    path = r'saved_data/250Hz_2024-11-17_18-55-28.npy'
    data = np.load(path)
    print(data)
    # Plot the signal
    plt.plot(data)
    plt.show()