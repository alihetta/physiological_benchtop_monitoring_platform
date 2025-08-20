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
from calculate_bpm import calculate_bpm
from calculate_spo2 import calculate_spo2

# Sets figure show to pop on default browser
pio.renderers.default = 'browser'

# parse data for calculating PTT
parsed_data = parse_csv('ECG and PPG data/trial1_ecg_ppg_gsr_deepbreathing.csv')
df_ecg = parsed_data['df_ecg']
t_raw = parsed_data['t_raw']
ir_raw = parsed_data['ir_raw']
df_ppg = parsed_data['df_ppg']
t_ecg = parsed_data['t_ecg']
red_raw = parsed_data['red_raw']
ecg_signal = parsed_data['ecg_signal']
t_gsr = parsed_data['t_gsr']
df_gsr = parsed_data['df_gsr']

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

spo2_df, spo2_time = calculate_spo2(ir_peaks_idx=ir_peaks_idx, red_peaks_idx=red_peaks_idx, red=red,ir=ir, t_uniform=t_uniform, desired_fs=250)


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


t_gsr = df_gsr["time_sec"].to_numpy()
gsr_signal = df_gsr["GSR"].to_numpy()

# From IR peaks
bpm_time_ir, bpm_clean_ir, bpm_smooth_ir = calculate_bpm(ir_peaks_idx, t_uniform)
# From ECG R-peaks
bpm_time_ecg, bpm_clean_ecg, bpm_smooth_ecg = calculate_bpm(rpeaks, t_interp)
# From IR troughs
bpm_time_trough, bpm_clean_trough, bpm_smooth_trough = calculate_bpm(ir_troughs_idx, t_uniform)


# === Create the base subplot layout ===
fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.07,
    subplot_titles=[
        "SpO₂ Over Time",
        "Heart Rate Over Time (IR, ECG, Trough)",
        "Pulse Transit Time (PTT) Over Time",
        "GSR Signal Over Time"
    ]
)

# === Plot 1: SpO₂ ===
try:
    fig.add_trace(go.Scatter(x=spo2_time, y=spo2_df['SpO2'], mode='lines', name='SpO₂', line=dict(color='green')), row=1, col=1)
    fig.update_yaxes(title_text="<b>SpO₂ (%)</b>", row=1, col=1)
except Exception as e:
    print("Skipping SpO₂ plot:", e)

# === Plot 2: Heart Rate ===
try:
    fig.add_trace(go.Scatter(x=bpm_time_ir, y=bpm_smooth_ir, mode='lines', name='BPM IR', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=bpm_time_ecg, y=bpm_smooth_ecg, mode='lines', name='BPM ECG', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=bpm_time_trough, y=bpm_smooth_trough, mode='lines', name='BPM Trough', line=dict(color='purple')), row=2, col=1)
    fig.update_yaxes(title_text="<b>BPM</b>", row=2, col=1)
except Exception as e:
    print("Skipping BPM plot:", e)

# === Plot 3: PTT ===
try:
    fig.add_trace(go.Scatter(x=ptt_peak_df['time'], y=ptt_peak_df['ptt'], mode='markers+lines', name='PTT Peaks', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Scatter(x=ptt_trough_df['time'], y=ptt_trough_df['ptt'], mode='markers+lines', name='PTT Troughs', line=dict(color='teal')), row=3, col=1)
    fig.update_yaxes(title_text="<b>PTT (s)</b>", row=3, col=1)
except Exception as e:
    print("Skipping PTT plot:", e)

# === Plot 4: GSR ===
try:
    fig.add_trace(go.Scatter(x=t_gsr, y=gsr_signal, mode='lines', name='GSR', line=dict(color='brown')), row=4, col=1)
    fig.update_yaxes(title_text="<b>GSR (µS)</b>", row=4, col=1)
except Exception as e:
    print("Skipping GSR plot:", e)

# === Add Exclusion Window Boxes (e.g., for Breath Holds) ===
for start, end in exclusion_windows:
    for row in range(1, 5):  # Apply to all 4 subplots
        fig.add_shape(
            type="rect",
            x0=start, x1=end,
            y0=0, y1=1,
            xref='x',
            yref=f'y{"" if row == 1 else row} domain',
            line=dict(color="red", width=2, dash="dash"),
            fillcolor="rgba(255, 0, 0, 0.1)",
            layer="below",
            row=row,
            col=1
        )

# === Global layout styling ===
fig.update_layout(
    height=1200,
    title="<b>Multimodal Signal Analysis</b>",
    title_font=dict(size=24),
    showlegend=True,
)

# Bold axes for all rows
for i in range(1, 5):
    fig.update_yaxes(title_font=dict(size=18, family='Arial Black'), tickfont=dict(size=16), row=i, col=1)
    fig.update_xaxes(title_font=dict(size=18, family='Arial Black'), tickfont=dict(size=16), row=i, col=1)

# Set x-axis title for last row
fig.update_xaxes(title_text="<b>Time (s)</b>", row=4, col=1)

fig.show()

