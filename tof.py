#!/usr/bin/env python3
"""
Raspberry Pi 4B VL53L0X-V2 Distance Sensor Program
This program demonstrates reading distance data from a VL53L0X-V2 sensor.
"""

import time
import board
import adafruit_vl53l0x

# Initialize I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize VL53L0X sensor
sensor = adafruit_vl53l0x.VL53L0X(i2c)

# Optional: Configure timing and measurement settings
# sensor.measurement_timing_budget = 200000  # microseconds, higher = more accurate but slower
# sensor.set_Vcsel_pulse_period(adafruit_vl53l0x.VL53L0X_VCSEL_PERIOD_PRE_RANGE, 18)
# sensor.set_Vcsel_pulse_period(adafruit_vl53l0x.VL53L0X_VCSEL_PERIOD_FINAL_RANGE, 14)

print("VL53L0X Distance Sensor Test")
print("Press Ctrl+C to exit")

try:
    while True:
        # Get distance reading in millimeters
        distance = sensor.range
        
        # Convert to centimeters for easier reading
        distance_cm = distance / 10.0
        
        print(f"Distance: {distance} mm ({distance_cm:.1f} cm)")
        
        # Adjust the delay according to your needs
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nProgram stopped by user")
except Exception as e:
    print(f"Error: {e}")