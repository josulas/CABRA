import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Dict
from scipy.signal import find_peaks


def find_wave_v(t_arr: np.ndarray,
                signal: np.ndarray,
                t_min: int = 5,
                t_max: int = 10,
                take_abs: bool = False,
                plot: bool = True,
                plot_settings: dict = None) -> Dict[str, int | float]:
    """
    Finds the largest amplitude of a signal within t_min < t < t_max.

    Args:
        t_arr (np.ndarray): Time array in milliseconds.
        signal (np.ndarray): Signal array (AEP signal).
        t_min (int): Initial time to analyze (ms).
        t_max (int): Final time to analyze (ms).
        take_abs (bool): Whether to take the absolute value of the signal (default False).
        plot (bool): Whether to plot the result (default True).
        plot_settings (dict): Custom settings for the plot, such as size and labels.

    Returns:
        Tuple[int, float, float]: (Index of peak, peak amplitude, amplitude range in the segment).
    """
    original_signal = np.copy(signal)
    if take_abs:
        signal = np.abs(signal - signal.mean())  # Normalize and take absolute value

    # Estimate sampling rate
    duration = t_arr[-1] - t_arr[0]
    fs = len(t_arr) / duration  # Sampling rate in samples per ms

    # Convert time to indices
    idx_min = int(fs * t_min)
    idx_max = int(fs * t_max)
    idx_min = max(0, idx_min)  # Ensure within bounds
    idx_max = min(len(signal), idx_max)

    if idx_min >= idx_max:
        raise ValueError("Invalid range: t_min should be less than t_max and within signal bounds.")

    # Find peak within the specified range
    idx_peak = np.argmax(signal[idx_min: idx_max]) + idx_min
    amp_peak = original_signal[idx_peak]
    amp_range = original_signal[idx_min: idx_max].max() - original_signal[idx_min: idx_max].min()

    # Find the start and end of the wave
    # First, identify the next peak using find_peaks()
    peaks, _ = find_peaks(original_signal[idx_peak + 1: idx_max])
    print(peaks)
    try:
        next_peak_idx = peaks[1] + idx_peak + 1
    except IndexError:
        next_peak_idx = idx_max
    
    try:
        wave_start_peak = np.argmin(original_signal[idx_min: idx_peak]) + idx_min
        wave_end_peak = np.argmin(original_signal[idx_peak: next_peak_idx]) + idx_peak
    except ValueError:
        wave_start_peak = idx_min
        wave_end_peak = idx_max
        
    features = {'peak_amplitude': amp_peak, 'amplitude_range': amp_range,
                'peak_time': t_arr[idx_peak], 'peak_index': idx_peak,
                'wave_start_time': t_arr[wave_start_peak], 'wave_start_index': wave_start_peak,
                'wave_end_time': t_arr[wave_end_peak], 'wave_end_index': wave_end_peak}

    # Plotting
    if plot:
        plot_settings = plot_settings or {}
        fig, ax = plt.subplots(figsize=plot_settings.get("figsize", (10, 5)))
        ax.plot(t_arr, original_signal, label="Signal")
        ax.plot(t_arr[wave_start_peak: wave_end_peak], original_signal[wave_start_peak: wave_end_peak], label="Segment")
        ax.plot(t_arr[idx_peak], original_signal[idx_peak], 'ro', label="Detected Peak")
        ax.set_xlabel(plot_settings.get("xlabel", "Time (ms)"))
        ax.set_ylabel(plot_settings.get("ylabel", "Amplitude (nV)"))
        ax.set_title(plot_settings.get("title", "Detected Wave V"))
        ax.legend()
        plt.show()

    return features


def threshold_detection(wave_v_features: dict,
                        amplitude_threshold: float =200., # [nv]
                        latency_range: Tuple[int, int] = (5, 8)) -> bool:
    """
    Rule-based threshold detection for perception inference.

    Args:
        wave_v_features (dict): Features of Wave V, including 'amplitude' and 'latency'.
        amplitude_threshold (float): Minimum peak amplitude (nV) to consider the signal significant.
        latency_range (Tuple[int, int]): Acceptable latency range in milliseconds.

    Returns:
        bool: True if criteria are met (sound perceived), False otherwise.
    """
    amplitude = wave_v_features['amplitude_range']
    latency = wave_v_features['peak_time']

    if amplitude >= amplitude_threshold and latency_range[0] <= latency <= latency_range[1]:
        return True  # Sound perceived
    return False  # Sound not perceived


def main():
    example_signal = np.load('simulated_signals/evoked.npy')
    fs = 8_000 # [Hz]
    t_arr = np.arange(0, len(example_signal) / fs, 1 / fs) * 1_000  # Time in milliseconds
    features = find_wave_v(t_arr, example_signal, t_min=5, t_max=20, plot=True)
    print(features)
    perceived = threshold_detection(features, amplitude_threshold=200, latency_range=(5, 8))
    print(f"Sound perceived: {perceived}")


if __name__ == '__main__':
    main()