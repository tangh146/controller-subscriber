#!/usr/bin/env python3
"""
Test script for integrating VL53L0X sensor and stepper motor
"""
import RPi.GPIO as GPIO
import time
import sys

# Import our modules
from stepper_motor import setup_stepper, dispense_until_distance, cleanup_stepper
from vl53l0x import initialize_sensor, get_distance, cleanup_sensor

# Target distance to stop at (in centimeters)
TARGET_DISTANCE_CM = 20

def main():
    """Main test function"""
    print("Testing VL53L0X + TB6600 Stepper Motor Integration")
    
    # Initialize sensors
    print("\n1. Initializing VL53L0X sensor...")
    try:
        if not initialize_sensor():
            print("Failed to initialize VL53L0X sensor")
            return False
    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        return False
        
    # Test distance reading
    print("\n2. Testing distance sensor...")
    try:
        for i in range(3):
            distance_mm = get_distance()
            distance_cm = distance_mm / 10.0
            print(f"Distance reading {i+1}: {distance_mm} mm ({distance_cm:.1f} cm)")
            time.sleep(0.5)
    except Exception as e:
        print(f"Error reading distance: {e}")
        return False
    
    # Initialize stepper
    print("\n3. Initializing stepper motor...")
    try:
        setup_stepper()
    except Exception as e:
        print(f"Error initializing stepper motor: {e}")
        return False
    
    # Test integrated function
    print(f"\n4. Testing stepper motor rotation until {TARGET_DISTANCE_CM}cm is reached...")
    print("Place an object in front of the sensor and slowly move it closer")
    print("The motor will stop when the object is detected at the target distance")
    print("Press Ctrl+C to stop the test at any time")
    
    input("Press Enter to begin the test...")
    
    try:
        result = dispense_until_distance(
            target_distance_cm=TARGET_DISTANCE_CM,
            max_steps=2000,  # Limit steps for testing
            speed_rpm=10,
            clockwise=True,
            get_distance_func=get_distance
        )
        
        if result:
            print("Test PASSED: Stepper stopped at target distance!")
        else:
            print("Test incomplete: Maximum steps reached without detecting target distance")
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nIntegration test completed successfully!")
        else:
            print("\nIntegration test failed!")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up
        print("\nCleaning up...")
        cleanup_sensor()
        cleanup_stepper()
        GPIO.cleanup()