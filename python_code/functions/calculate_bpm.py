import numpy as np
import pandas as pd

def calculate_bpm(peak_indices, time_vector, min_bpm=40, max_bpm=150, smoothing_window=20):
    """
    Calculate heart rate (BPM) from peak indices and time vector.

    Parameters:
    - peak_indices (array-like): Indices of peaks or troughs in the signal
    - time_vector (array-like): Time values corresponding to the signal
    - min_bpm (float): Minimum BPM threshold for valid heart rate (default: 40)
    - max_bpm (float): Maximum BPM threshold for valid heart rate (default: 150)
    - smoothing_window (int): Window size for median smoothing (default: 20)

    Returns:
    - bpm_time (np.ndarray): Time values for each BPM value
    - bpm_clean (np.ndarray): Cleaned/interpolated BPM values
    - bpm_smooth (np.ndarray): Smoothed BPM values
    """
    # Get time values for each peak
    peak_times = time_vector[peak_indices]

    # Calculate intervals between peaks in seconds
    intervals = np.diff(peak_times)

    # Convert to BPM
    bpm = 60 / intervals
    bpm_time = peak_times[:-1]  # time corresponding to each BPM

    # Clean values outside reasonable range
    bpm_clean = np.where((bpm < min_bpm) | (bpm > max_bpm), np.nan, bpm)
    bpm_clean = pd.Series(bpm_clean).interpolate().to_numpy()

    # Apply rolling median smoothing
    bpm_smooth = pd.Series(bpm_clean).rolling(window=smoothing_window, center=True, min_periods=1).median().to_numpy()

    return bpm_time, bpm_clean, bpm_smooth
