import numpy as np
import pandas as pd

def calculate_spo2(ir_peaks_idx, red_peaks_idx, red, ir, t_uniform, desired_fs, match_window_ms=50, smoothing_window=20):
    """
    Calculates SpO₂ from IR and Red PPG signals using AC/DC ratio.

    Parameters:
    - ir_peaks_idx (array-like): Indices of IR peaks
    - red_peaks_idx (array-like): Indices of Red peaks
    - red (np.ndarray): Red light PPG signal (interpolated and smoothed)
    - ir (np.ndarray): IR light PPG signal (interpolated and smoothed)
    - t_uniform (np.ndarray): Time vector corresponding to red/ir signals
    - desired_fs (float): Sampling frequency of red/ir signals
    - match_window_ms (int): Matching window in milliseconds (default: 50ms)
    - smoothing_window (int): Window size for rolling median (default: 20)

    Returns:
    - spo2_df (pd.DataFrame): DataFrame with columns ['Time', 'SpO2'] (smoothed and rounded)
    - spo2_time (np.ndarray): Time points associated with each SpO₂ value
    """

    window = int((match_window_ms / 1000.0) * desired_fs)

    # === Match IR and Red Peaks ===
    matched_ir_peaks = []
    matched_red_peaks = []

    for ir_idx in ir_peaks_idx:
        candidates = red_peaks_idx[(red_peaks_idx >= ir_idx - window) & (red_peaks_idx <= ir_idx + window)]
        if len(candidates) > 0:
            closest_red = candidates[np.argmin(np.abs(candidates - ir_idx))]
            matched_ir_peaks.append(ir_idx)
            matched_red_peaks.append(closest_red)

    # === SpO₂ Calculation ===
    spo2_list = []
    spo2_time = []

    for i in range(len(matched_ir_peaks) - 1):
        ir_start = matched_ir_peaks[i]
        ir_end = matched_ir_peaks[i + 1]
        red_idx = matched_red_peaks[i]

        red_seg = red[red_idx:ir_end]
        ir_seg = ir[ir_start:ir_end]

        if len(red_seg) < 2 or len(ir_seg) < 2:
            continue

        ac_red = np.max(red_seg) - np.min(red_seg)
        dc_red = np.mean(red_seg)
        ac_ir = np.max(ir_seg) - np.min(ir_seg)
        dc_ir = np.mean(ir_seg)

        if dc_red == 0 or dc_ir == 0:
            continue

        R = (ac_red / dc_red) / (ac_ir / dc_ir)
        spo2 = 110 - 25 * R

        if 70 <= spo2 <= 110:
            spo2_list.append(spo2)
            spo2_time.append(t_uniform[ir_start])

    # === Final Output ===
    spo2_df = pd.DataFrame({
        'Time': spo2_time,
        'SpO2': spo2_list
    })

    spo2_df['SpO2'] = spo2_df['SpO2'].round()
    spo2_df['SpO2'] = spo2_df['SpO2'].rolling(window=smoothing_window, center=True, min_periods=1).median()

    return spo2_df, np.array(spo2_time)
