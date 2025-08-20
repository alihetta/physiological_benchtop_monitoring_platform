#include <Wire.h>
#include "MAX30105.h"

MAX30105 particleSensor;

void setup()
{
  Serial.begin(230400);
  while (!Serial);

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD))
  {
    Serial.println("MAX30105 not found. Check wiring.");
    while (1);
  }

  // Best signal configuration
  particleSensor.setup(0x1F, 1, 2, 400, 411, 4096);
  particleSensor.setFIFOAverage(1);
  particleSensor.enableFIFORollover();
  particleSensor.setFIFOAlmostFull(64);

  delay(2000); // Let sensor stabilize
}

void loop()
{
  particleSensor.check();

  while (particleSensor.available())
  {
    uint32_t red = particleSensor.getFIFORed();
    uint32_t ir = particleSensor.getFIFOIR();
    uint32_t time = millis();

    // Tab-separated for Arduino Serial Plotter
    
    Serial.print("PPG,");
    Serial.print(time);
    Serial.print(",");
    Serial.print(red);
    Serial.print(",");
    Serial.println(ir);

    particleSensor.nextSample();
  }
}