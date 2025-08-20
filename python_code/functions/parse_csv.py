import pandas as pd
import csv

def parse_csv(filepath):
    # === Step 1: Initialize storage ===
    ecg_timestamps, ecg_data = [], []
    ppg_timestamps, red_light, infrared_light = [], [], []
    gsr_timestamps, gsr_data = [], []

    ppg_skipped = ecg_skipped = gsr_skipped = 0

    # === Step 2: Read and Parse CSV Properly ===
    with open(filepath, 'r', newline='') as file:
        reader = csv.reader(file)

        for row in reader:
            if not row or len(row) < 2:
                continue  # skip empty or malformed rows

            tag = row[0].replace(',', '').strip().lower()

            try:
                if tag == 'ecg' and len(row) >= 3:
                    ts = float(row[1].replace(',', '').strip())
                    val = float(row[2].replace(',', '').strip())
                    ecg_timestamps.append(ts)
                    ecg_data.append(val)

                elif tag == 'ppg' and len(row) >= 4:
                    ts = float(row[1].replace(',', '').strip())
                    red = float(row[2].replace(',', '').strip())
                    ir_str = row[3].replace(',', '').strip()
                    if ir_str == '':
                        raise ValueError("Missing IR value")
                    ir = float(ir_str)
                    ppg_timestamps.append(ts)
                    red_light.append(red)
                    infrared_light.append(ir)

                elif tag == 'gsr' and len(row) >= 3:
                    ts = float(row[1].replace(',', '').strip())
                    val = float(row[2].replace(',', '').strip())
                    gsr_timestamps.append(ts)
                    gsr_data.append(val)

            except ValueError:
                if tag == 'ecg':
                    ecg_skipped += 1
                elif tag == 'ppg':
                    ppg_skipped += 1
                elif tag == 'gsr':
                    gsr_skipped += 1

    # === Step 3: Create DataFrames ===
    df_ecg = pd.DataFrame({'Time Stamp': ecg_timestamps, 'ECG': ecg_data})
    df_ppg = pd.DataFrame({'Time Stamp': ppg_timestamps, 'Red Light': red_light, 'IR': infrared_light})
    df_gsr = pd.DataFrame({'Time Stamp': gsr_timestamps, 'GSR': gsr_data})

    # === Step 4: Convert Time to Seconds from Start ===
    if not df_ppg.empty:
        df_ppg["time_sec"] = (df_ppg["Time Stamp"] - df_ppg["Time Stamp"].iloc[0]) / 1000.0
        t_raw = df_ppg["time_sec"].to_numpy()
        red_raw = df_ppg["Red Light"].to_numpy()
        ir_raw = df_ppg["IR"].to_numpy()
    else:
        print("⚠️ Warning: df_ppg is empty after parsing!")
        t_raw = red_raw = ir_raw = None

    if not df_ecg.empty:
        df_ecg["time_sec"] = (df_ecg["Time Stamp"] - df_ecg["Time Stamp"].iloc[0]) / 1000.0
        t_ecg = df_ecg["time_sec"].to_numpy()
        ecg_signal = df_ecg["ECG"].to_numpy()
    else:
        print("⚠️ Warning: df_ecg is empty after parsing!")
        t_ecg = ecg_signal = None

    if not df_gsr.empty:
        df_gsr["time_sec"] = (df_gsr["Time Stamp"] - df_gsr["Time Stamp"].iloc[0]) / 1000.0
        t_gsr = df_gsr["time_sec"].to_numpy()
        gsr_signal = df_gsr["GSR"].to_numpy()
    else:
        print("⚠️ Warning: df_gsr is empty after parsing!")
        t_gsr = gsr_signal = None

    # === Step 5: Summary ===
    print(f"✅ Finished parsing.")
    print(f"PPG: {len(ppg_timestamps)} rows parsed, {ppg_skipped} skipped.")
    print(f"ECG: {len(ecg_timestamps)} rows parsed, {ecg_skipped} skipped.")
    print(f"GSR: {len(gsr_timestamps)} rows parsed, {gsr_skipped} skipped.")

    return {
        'df_ecg': df_ecg,
        'df_ppg': df_ppg,
        'df_gsr': df_gsr,
        't_raw': t_raw,
        'red_raw': red_raw,
        'ir_raw': ir_raw,
        't_ecg': t_ecg,
        'ecg_signal': ecg_signal,
        't_gsr': t_gsr,
        'gsr_signal': gsr_signal
    }
