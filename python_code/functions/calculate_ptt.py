import numpy as np
import pandas as pd

def calculate_ptt(t_interp, t_uniform, rpeaks, ir_feature_idx, exclusion_windows=None):
    # Match ECG R-peaks to future IR events (peaks or troughs)
    ecg_peak_times = t_interp[rpeaks]
    ir_event_times = t_uniform[ir_feature_idx]

    matched_ecg_times = []
    matched_ir_times = []
    ptt_values = []

    for ecg_time in ecg_peak_times:
        future_ir = ir_event_times[ir_event_times > ecg_time]
        if len(future_ir) > 0:
            ir_time = future_ir[0]
            matched_ecg_times.append(ecg_time)
            matched_ir_times.append(ir_time)
            ptt_values.append(ir_time - ecg_time)

    # Rolling mean smoothing
    ptt_values = pd.Series(ptt_values).rolling(window=5, center=True, min_periods=1).mean()
    valid_mask = ptt_values <= 0.8
    ptt_values = ptt_values[valid_mask].reset_index(drop=True)
    matched_ecg_times = np.array(matched_ecg_times)[valid_mask].tolist()

    # Full PTT dataframe for plotting (all time points)
    ptt_df = pd.DataFrame({'time': matched_ecg_times, 'ptt': ptt_values})

    # For average-only, apply exclusions
    ptt_df_avg = ptt_df.copy()
    if exclusion_windows:
        for start, end in exclusion_windows:
            ptt_df_avg = ptt_df_avg[(ptt_df_avg['time'] < start) | (ptt_df_avg['time'] > end)]

    ptt_avg = ptt_df_avg['ptt'].mean()

    # Return both full and filtered versions
    return ptt_df, ptt_avg

