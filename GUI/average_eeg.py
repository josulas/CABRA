import numpy as np


def average_EEG(X: np.ndarray, mode: str='homogenous', eps=1e-6) -> np.ndarray:
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
    VALID_MODES = {'homogenous', 'amp', 'var', 'both'}
    if mode not in VALID_MODES:
        raise ValueError(F"{mode} is not a valid mode. Should be: {''.join(VALID_MODES)}")

    if mode == 'homogenous':
        return np.mean(X, axis=0)

    # Find amplitudes
    s = np.mean(X, axis = 0)
    a = X.dot(s.T)
    a[a==0] = eps

    # Find variances
    M = X.shape[1]
    V = np.var(X[:, -int(0.4*M):], axis=1)
    V[V==0] = eps

    # Get weights and average
    if mode == 'amp':
        w = a / np.sum(a**2)
    elif mode == 'var':
        w = (1/V) / (np.sum(1/V))
    elif mode == 'both':
        w = (a/V) / (np.sum(a**2/V))

    return w.T.dot(X/np.sum(w))

if __name__ == "__main__":
    X = np.random.rand(10, 100)
    print(average_EEG(X, mode='homogenous'))
    print(average_EEG(X, mode='amp'))
    print(average_EEG(X, mode='var'))
    print(average_EEG(X, mode='both'))
    Zeroes = np.zeros((10, 100))
    print(average_EEG(Zeroes, mode='homogenous'))
    print(average_EEG(Zeroes, mode='amp'))
    print(average_EEG(Zeroes, mode='var'))
    print(average_EEG(Zeroes, mode='both'))
