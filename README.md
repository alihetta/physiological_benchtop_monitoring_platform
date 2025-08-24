# Physiological Monitoring Platform

**Overview:**
 This project provides a **multimodal physiological monitoring system** that acquires, processes, and visualizes signals from:
1. **Electrocardiography (ECG)**
2. **Photoplethysmography (PPG: Red & Infrared)**
3. **Galvanic Skin Response (GSR)**

The platform integrates **Arduino firmware** for data acquisition with a **Python analysis pipeline** for advanced signal processing and visualization.

**Key features:**
1. Real-time acquisition of ECG, PPG, and GSR signals  
2. Signal interpolation, smoothing, and peak/trough detection  
3. Computation of **SpO₂, Heart Rate (BPM), and Pulse Transit Time (PTT)**  
4. Multimodal visualization in an interactive dashboard  

---

**System Architecture**
1. Firmware (finalized_ecg_ppg_gsr_firmware.ino)  
   - Runs on Arduino-compatible hardware  
   - Collects raw ECG, PPG (IR + Red), and GSR signals  
   - Streams data via serial for logging and processing  

2. Python Analysis Pipeline (ppg_ecg_gsr_final_code.py)  
   - Parses raw CSV data from acquisition device  
   - Applies Gaussian smoothing and uniform resampling  
   - Detects:
     - PPG peaks/troughs  
     - ECG R-peaks  
   - Computes:
     - SpO₂ (ratio-of-ratios method)  
     - Heart Rate (from ECG R-peaks, IR peaks, and troughs)  
     - PTT (ECG-to-PPG timing differences)  
   - Produces interactive plots (SpO₂, BPM, PTT, GSR)  

---
**Outputs:**
 The Python script generates an interactive dashboard with:
1. SpO₂ (%) over time
2. Heart Rate (BPM) from ECG and PPG  
3. Pulse Transit Time (PTT) trends  
4. GSR signal dynamics 
5. Highlighted exclusion windows (e.g., breath-holds)  

---
**Prerequisites**
- Hardware: Arduino-compatible microcontroller, ECG electrodes, PPG sensor (e.g., MAX30102), GSR sensor  
- Software:  
  - Arduino IDE  
  - Python 3.9+ with dependencies:
    ```bash
    pip install numpy pandas matplotlib scipy plotly biosppy
    ```

**Running the System**
1. Upload the Arduino firmware (`.ino`) to your microcontroller.  
2. Record physiological data and save as CSV.  
3. Run the Python analysis script:
   ```bash
   python ppg_ecg_gsr_final_code.py
