import numpy as np
from scipy.signal import find_peaks, detrend

def ir_and_red_peaktrough_detection(red_smoothed, ir_smoothed,
                                  red_prominence=200, ir_prominence=350,
                                  min_thresh=70000, max_thresh=150000):
    # === Detrend the smoothed signals ===
    red_detrended = detrend(red_smoothed)
    ir_detrended = detrend(ir_smoothed)

    # === Red Signal Peak/Trough Detection ===
    def detect_peaks_and_troughs_red(signal, min_thresh=70000, max_thresh=150000, prominence=200):
        peaks, _ = find_peaks(signal, prominence=prominence)
        peaks = [idx for idx in peaks if min_thresh < signal[idx] < max_thresh]
        troughs, _ = find_peaks(-signal, prominence=prominence)
        troughs = [idx for idx in troughs if min_thresh < signal[idx] < max_thresh]
        return np.array(peaks), np.array(troughs)

    # === IR Signal Peak/Trough Detection ===
    def detect_peaks_and_troughs_ir(signal, min_thresh=70000, max_thresh=150000, prominence=350):
        peaks, _ = find_peaks(signal, prominence=prominence)
        peaks = [idx for idx in peaks if min_thresh < signal[idx] < max_thresh]
        troughs, _ = find_peaks(-signal, prominence=prominence)
        troughs = [idx for idx in troughs if min_thresh < signal[idx] < max_thresh]
        return np.array(peaks), np.array(troughs)

    # === Apply detection ===
    red_peaks_idx, red_troughs_idx = detect_peaks_and_troughs_red(red_smoothed, min_thresh, max_thresh, red_prominence)
    ir_peaks_idx, ir_troughs_idx = detect_peaks_and_troughs_ir(ir_smoothed, min_thresh, max_thresh, ir_prominence)

    return {
        'red_detrended': red_detrended,
        'ir_detrended': ir_detrended,
        'red_peaks_idx': red_peaks_idx,
        'red_troughs_idx': red_troughs_idx,
        'ir_peaks_idx': ir_peaks_idx,
        'ir_troughs_idx': ir_troughs_idx
    }