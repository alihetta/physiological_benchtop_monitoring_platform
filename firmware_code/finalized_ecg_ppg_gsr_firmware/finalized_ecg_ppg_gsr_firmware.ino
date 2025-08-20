#include "protocentralAds1292r.h"
#include "ecgRespirationAlgo.h"
#include <SPI.h>
#include <Wire.h>
#include "MAX30105.h"

MAX30105 particleSensor;

volatile uint8_t globalHeartRate = 0;
volatile uint8_t globalRespirationRate = 0;

const int ADS1292_DRDY_PIN = 6;
const int ADS1292_CS_PIN = 7;
const int ADS1292_START_PIN = 5;
const int ADS1292_PWDN_PIN = 4;

int16_t ecgWaveBuff = 0, ecgFilterout = 0;
int16_t resWaveBuff = 0, respFilterout = 0;

ads1292r ADS1292R;
ecg_respiration_algorithm ECG_RESPIRATION_ALGORITHM;

// === GSR Variables ===
const int GSR_PIN = A0;
int gsr_average = 0;

#define GSR_SAMPLES 10
int gsrSampleCount = 0;
long gsrRunningSum = 0;
unsigned long lastGSRReadTime = 0;
unsigned long gsrPrintTime = 0;

// === PPG timestamping ===
const float PPG_SAMPLE_INTERVAL_MS = 1000.0 / 100.0;  // 100 Hz -> 10 ms interval
unsigned long ppgStartTime = 0;
unsigned long ppgSampleCount = 0;

void setup() {
  Serial.begin(230400);
  while (!Serial);

  // === ECG Setup ===
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE1);
  SPI.setClockDivider(SPI_CLOCK_DIV16);

  pinMode(ADS1292_DRDY_PIN, INPUT);
  pinMode(ADS1292_CS_PIN, OUTPUT);
  pinMode(ADS1292_START_PIN, OUTPUT);
  pinMode(ADS1292_PWDN_PIN, OUTPUT);

  ADS1292R.ads1292Init(ADS1292_CS_PIN, ADS1292_PWDN_PIN, ADS1292_START_PIN);

  // === PPG Setup ===
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30105 not found. Check wiring.");
    while (1);
  }

  // MAX30105 setup: 400Hz requested, but expect ~100Hz actual
  particleSensor.setup(0x1F, 1, 2, 400, 411, 4096);
  particleSensor.setFIFOAverage(1);
  particleSensor.enableFIFORollover();
  particleSensor.setFIFOAlmostFull(64);

  delay(2000); // Let sensors stabilize
}

// === GSR: Non-blocking Averaging ===
void updateGSR() {
  if (millis() - lastGSRReadTime >= 5) {  // Read one sample every 5 ms
    lastGSRReadTime = millis();

    gsrRunningSum += analogRead(GSR_PIN);
    gsrSampleCount++;

    if (gsrSampleCount >= GSR_SAMPLES) {
      gsr_average = gsrRunningSum / GSR_SAMPLES;
      gsrRunningSum = 0;
      gsrSampleCount = 0;

      gsrPrintTime = millis();
      Serial.print("GSR,");
      Serial.print(gsrPrintTime);
      Serial.print(",");
      Serial.println(gsr_average);
    }
  }
}

void loop() {
  // === ECG: DRDY-driven sampling ===
  if (digitalRead(ADS1292_DRDY_PIN) == LOW) {
    unsigned long ecgTimestamp = millis();  // Timestamp as close as possible to DRDY LOW

    ads1292OutputValues ecgRespirationValues;
    boolean ret = ADS1292R.getAds1292EcgAndRespirationSamples(
      ADS1292_DRDY_PIN, ADS1292_CS_PIN, &ecgRespirationValues);

    if (ret) {
      long rawECG = ecgRespirationValues.sDaqVals[1];
      Serial.print("ECG,");
      Serial.print(ecgTimestamp);
      Serial.print(",");
      Serial.println(rawECG);
      ecgWaveBuff = (int16_t)(ecgRespirationValues.sDaqVals[1] >> 8);  // ECG from channel 1
      resWaveBuff = (int16_t)(ecgRespirationValues.sresultTempResp >> 8);

      if (!ecgRespirationValues.leadoffDetected) {
        ECG_RESPIRATION_ALGORITHM.ECG_ProcessCurrSample(&ecgWaveBuff, &ecgFilterout);
        ECG_RESPIRATION_ALGORITHM.QRS_Algorithm_Interface(ecgFilterout, &globalHeartRate);
      } else {
        ecgFilterout = 0;
        respFilterout = 0;
      }
    }
  }

  // PPG (MAX30105): Sample + timestamp at ~100 Hz ===
  particleSensor.check();

  while (particleSensor.available()) {
    uint32_t red = particleSensor.getFIFORed();
    uint32_t ir = particleSensor.getFIFOIR();
    unsigned long ppgTimestamp = millis();

    Serial.print("PPG,");
    Serial.print(ppgTimestamp);
    Serial.print(",");
    Serial.print(red);
    Serial.print(",");
    Serial.println(ir);

    particleSensor.nextSample();
  }
  // === GSR: Background Sampling ===
  updateGSR();
}
