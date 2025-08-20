import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import plotly.graph_objs as go
import plotly.io as pio
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, detrend
from scipy.signal import correlate
from scipy.stats import pearsonr
from plotly.subplots import make_subplots
import csv
from biosppy.signals import ecg
from calculate_ptt import calculate_ptt
from parse_csv import parse_csv
from ir_and_red_peaktrough_detection import ir_and_red_peaktrough_detection

# Sets figure show to pop on default browser
pio.renderers.default = 'browser'

# parse data for calculating PTT
parsed_data = parse_csv('ECG and PPG data/ecg_ppg_74s_b_46s_h_94s_b_ali_trial4.csv')
df_ecg = parsed_data['df_ecg']
t_raw = parsed_data['t_raw']
ir_raw = parsed_data['ir_raw']
df_ppg = parsed_data['df_ppg']
t_ecg = parsed_data['t_ecg']
red_raw = parsed_data['red_raw']
ecg_signal = parsed_data['ecg_signal']

# Interpolate to uniform sampling of 250Hz on Raw IR and Red Light Data
desired_fs = 250  # Hz
dt = 1 / desired_fs
t_uniform = np.arange(t_raw[0], t_raw[-1], dt)
red_interp = interp1d(t_raw, red_raw, kind='linear', fill_value="extrapolate")
ir_interp = interp1d(t_raw, ir_raw, kind='linear', fill_value="extrapolate")
red = red_interp(t_uniform)
ir = ir_interp(t_uniform)

# Apply 1D Gaussian smoothing, keep sigma 6 for optimal smoothing on Raw IR and Redlight data
red_smoothed = gaussian_filter1d(red, sigma=6)
ir_smoothed = gaussian_filter1d(ir, sigma=6)

#Peak and Trough Detection for IR and Red Light Signal and Raw Data Plot
ppg_peak_detection_results = ir_and_red_peaktrough_detection(red_smoothed, ir_smoothed, red_prominence=100, ir_prominence=300)
red_peaks_idx = ppg_peak_detection_results['red_peaks_idx']
ir_troughs_idx = ppg_peak_detection_results['ir_troughs_idx']
red_troughs_idx = ppg_peak_detection_results['red_troughs_idx']
ir_peaks_idx = ppg_peak_detection_results['ir_peaks_idx']

#Plot Raw Data of PPG with marked Peak and Trough Detection
fig = go.Figure()
fig.add_trace(go.Scatter(x=t_uniform, y=red, mode='lines', name='Red Raw', line=dict(color='red')))
fig.add_trace(go.Scatter(x=t_uniform[red_peaks_idx], y=red[red_peaks_idx], mode='markers',
                         name='Red Peaks', marker=dict(symbol='triangle-up', color='black')))
fig.add_trace(go.Scatter(x=t_uniform[red_troughs_idx], y=red[red_troughs_idx], mode='markers',
                         name='Red Troughs', marker=dict(symbol='triangle-down', color='black')))
fig.add_trace(go.Scatter(x=t_uniform, y=ir, mode='lines', name='IR Raw', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=t_uniform[ir_peaks_idx], y=ir[ir_peaks_idx], mode='markers',
                         name='IR Peaks', marker=dict(symbol='triangle-up', color='blue')))
fig.add_trace(go.Scatter(x=t_uniform[ir_troughs_idx], y=ir[ir_troughs_idx], mode='markers',
                         name='IR Troughs', marker=dict(symbol='triangle-down', color='blue')))
fig.update_layout(
    title="Raw Signals with Threshold-Filtered Peaks and Troughs",
    xaxis_title="Time (s)",
    yaxis_title="Amplitude",
    hovermode="x unified"
)
fig.show()

# ECG Signal Interpolation and R peak Detection
fs_desired = 125  # target sampling rate
t_min = t_ecg[0]
t_max = t_ecg[-1]
t_interp = np.arange(t_min, t_max, 1 / fs_desired)
interpolator = interp1d(t_ecg, ecg_signal, kind='slinear', fill_value='extrapolate')
ecg_interp = interpolator(t_interp)
out = ecg.ecg(signal=ecg_interp, sampling_rate=fs_desired, show=False)
rpeaks = out['rpeaks']

exclusion_windows = [(74, 120)]
ptt_peak_df, ptt_peak_avg = calculate_ptt(t_interp, t_uniform, rpeaks, ir_peaks_idx, exclusion_windows=[(74, 120)])
ptt_trough_df, ptt_trough_avg = calculate_ptt(t_interp, t_uniform, rpeaks, ir_troughs_idx, exclusion_windows=[(74, 120)])

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=ptt_trough_df['time'],
    y=ptt_trough_df['ptt'],
    mode='lines+markers',
    name='PTT (Trough)',
    line=dict(color='blue')
))

fig.add_trace(go.Scatter(
    x=ptt_peak_df['time'],
    y=ptt_peak_df['ptt'],
    mode='lines+markers',
    name='PTT (Peak)',
    line=dict(color='red')
))

# === 4. Add average lines
fig.add_shape(type='line',
              x0=ptt_trough_df['time'].min(), x1=ptt_trough_df['time'].max(),
              y0=ptt_trough_avg, y1=ptt_trough_avg,
              line=dict(color='blue', dash='dash'))

fig.add_shape(type='line',
              x0=ptt_peak_df['time'].min(), x1=ptt_peak_df['time'].max(),
              y0=ptt_peak_avg, y1=ptt_peak_avg,
              line=dict(color='red', dash='dash'))

# === 5. Add breath-hold shading
for start, end in exclusion_windows:
    fig.add_shape(
        type="rect",
        x0=start, x1=end,
        y0=0,
        y1=max(ptt_trough_df['ptt'].max(), ptt_peak_df['ptt'].max()),
        fillcolor="rgba(144,238,144,0.2)",
        line=dict(color="green", dash="dash"),
        layer="below"
    )

# === 6. Final layout
fig.update_layout(
    title="<b>Pulse Transit Time: Trough vs Peak</b>",
    xaxis=dict(title="<b>ECG R-Peak Time (s)</b>", tickfont=dict(size=18, family="Arial Black")),
    yaxis=dict(title="<b>Pulse Transit Time (s)</b>", tickfont=dict(size=18, family="Arial Black")),
    hovermode="x unified"
)

fig.show()

# === Matched ECG R-peaks to IR Troughs: Annotated Plot ===

# Step 1: Normalize IR signal to match ECG scale
ir_min, ir_max = np.min(ir), np.max(ir)
ecg_min, ecg_max = np.min(ecg_interp), np.max(ecg_interp)
ir_scaled = (ir - ir_min) / (ir_max - ir_min) * (ecg_max - ecg_min) + ecg_min

# Step 2: Compute IR trough times and indices
ptt_trough_df['ppg_time'] = ptt_trough_df['time'] + ptt_trough_df['ptt']
matched_r_idxs = [np.argmin(np.abs(t_interp - t)) for t in ptt_trough_df['time']]
matched_ir_idxs = [np.argmin(np.abs(t_uniform - t)) for t in ptt_trough_df['ppg_time']]

# Step 3: Create figure
fig_match_troughs = go.Figure()

# Plot ECG and scaled IR
fig_match_troughs.add_trace(go.Scatter(x=t_interp, y=ecg_interp, name="ECG", line=dict(color='green')))
fig_match_troughs.add_trace(go.Scatter(x=t_uniform, y=ir_scaled, name="IR (scaled)", line=dict(color='orange')))

# Step 4: Plot matches with numbered labels and dashed lines
for i, (r_idx, ir_idx) in enumerate(zip(matched_r_idxs, matched_ir_idxs)):
    fig_match_troughs.add_trace(go.Scatter(
        x=[t_interp[r_idx]],
        y=[ecg_interp[r_idx]],
        mode='markers+text',
        text=[str(i + 1)],
        textposition='top center',
        marker=dict(color='blue', size=8),
        name='R-peak'
    ))

    fig_match_troughs.add_trace(go.Scatter(
        x=[t_uniform[ir_idx]],
        y=[ir_scaled[ir_idx]],
        mode='markers+text',
        text=[str(i + 1)],
        textposition='bottom center',
        marker=dict(color='red', size=8),
        name='IR trough'
    ))

    fig_match_troughs.add_shape(
        type="line",
        x0=t_interp[r_idx], x1=t_uniform[ir_idx],
        y0=ecg_interp[r_idx], y1=ir_scaled[ir_idx],
        line=dict(color="gray", dash="dot", width=1),
        layer="below"
    )

# Step 5: Layout
fig_match_troughs.update_layout(
    title="<b>Matched ECG R-peaks to IR Troughs (Numbered, Scaled IR)</b>",
    xaxis_title="Time (s)",
    yaxis_title="Amplitude (ECG & Normalized IR)",
    hovermode="x unified"
)

fig_match_troughs.show()
