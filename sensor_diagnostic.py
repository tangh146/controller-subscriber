#!/usr/bin/env python3
"""
VL53L0X Sensor Diagnostic Tool
This script helps troubleshoot issues with the VL53L0X distance sensor.
"""

import time
import sys
import RPi.GPIO as GPIO
from vl53l0x import initialize_sensor, get_distance, test_sensor, cleanup_sensor

# Number of continuous readings to perform
NUM_READINGS = 20

def main():
    """Main diagnostic function"""
    print("VL53L0X Sensor Diagnostic Tool")
    print("==============================")
    
    # Step 1: Initialize the sensor
    print("\nStep 1: Initializing sensor...")
    try:
        if initialize_sensor():
            print("✓ Sensor initialization successful")
        else:
            print("✗ Sensor initialization failed")
            return
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        return
    
    # Step 2: Test sensor reliability
    print("\nStep 2: Testing sensor reliability...")
    sensor_working = test_sensor(num_readings=5, delay=0.5)
    
    if not sensor_working:
        print("✗ Sensor reliability test failed")
        print("\nPossible issues:")
        print("1. Incorrect wiring connections")
        print("2. I2C address conflict")
        print("3. Power supply issues")
        print("4. Damaged sensor")
        return
    
    # Step 3: Continuous measurement mode
    print("\nStep 3: Starting continuous measurement...")
    print("Place objects at different distances to test the sensor readings")
    print("Press Ctrl+C to stop\n")
    
    try:
        validations = 0
        total_readings = 0
        start_time = time.time()
        
        # Take readings for a while
        while total_readings < NUM_READINGS:
            distance_mm = get_distance()
            distance_cm = distance_mm / 10.0
            
            # Validate reading
            if distance_mm > 0:
                validations += 1
                status = "VALID"
            else:
                status = "INVALID"
                
            # Print with timestamp
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] Distance: {distance_mm} mm ({distance_cm:.1f} cm) - {status}")
            
            total_readings += 1
            time.sleep(0.5)
            
        # Print summary
        reliability = (validations / total_readings) * 100
        print(f"\nReliability: {reliability:.1f}% ({validations}/{total_readings} valid readings)")
        
        # Step 4: Testing target distance detection
        print("\nStep 4: Testing target distance detection (20cm)")
        print("Place an object exactly 20cm from the sensor")
        input("Press Enter when ready...")
        
        target_tests = 5
        target_hits = 0
        
        for i in range(target_tests):
            distance_mm = get_distance()
            distance_cm = distance_mm / 10.0
            
            print(f"Reading {i+1}: {distance_mm} mm ({distance_cm:.1f} cm)")
            
            # Check if it's close to our target (20cm ± 2cm)
            if 180 <= distance_mm <= 220:
                target_hits += 1
                print("✓ Target distance detected!")
            else:
                print("✗ Not at target distance")
                
            time.sleep(0.5)
            
        target_accuracy = (target_hits / target_tests) * 100
        print(f"\nTarget detection accuracy: {target_accuracy:.1f}% ({target_hits}/{target_tests})")
        
        # Final verdict
        if reliability > 80 and target_accuracy > 60:
            print("\n✓ Sensor appears to be WORKING CORRECTLY")
        elif reliability > 60 or target_accuracy > 40:
            print("\n⚠ Sensor is PARTIALLY WORKING but may have issues")
        else:
            print("\n✗ Sensor is NOT WORKING RELIABLY")
            
        print("\nRecommendations:")
        if reliability < 80:
            print("- Check wiring connections")
            print("- Ensure stable power supply")
            print("- Try different I2C pull-up resistors")
        if target_accuracy < 60:
            print("- Calibrate the sensor")
            print("- Check for interference sources")
            print("- Ensure stable mounting of the sensor")
            
    except KeyboardInterrupt:
        print("\nDiagnostic stopped by user")
    except Exception as e:
        print(f"\nError during diagnostic: {e}")
    
    # Cleanup
    cleanup_sensor()
    print("\nDiagnostic complete")
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        try:
            cleanup_sensor()
        except:
            pass