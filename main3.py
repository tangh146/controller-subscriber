#!/usr/bin/env python3
"""
main.py - Combines stepper motor control with ToF distance sensor
Functionality:
- Runs the stepper motor continuously
- Stops the motor when an object is detected at 20cm or closer
"""

import time
import argparse
# Import functions from stepper motor and ToF sensor files
from smotor2 import setup, rotate_degrees, cleanup
from tof import initialize_sensor, get_distance

# Configuration
DISTANCE_THRESHOLD = 20.0  # in cm (20cm threshold as specified)
MOTOR_SPEED = 10.0  # RPM
CHECK_INTERVAL = 0.1  # seconds between distance checks while motor is running
MOTOR_STEP_ANGLE = 10.0  # degrees to rotate per step (smaller value = more frequent checks)

def main():
    """
    Main function that controls the motor based on distance sensor readings
    """
    parser = argparse.ArgumentParser(description='Control stepper motor based on ToF sensor')
    
    # Add arguments
    parser.add_argument('-s', '--speed', type=float, default=MOTOR_SPEED,
                      help=f'Motor speed in RPM (default: {MOTOR_SPEED})')
    parser.add_argument('-c', '--clockwise', action='store_true',
                      help='Rotate clockwise (default: counterclockwise)')
    parser.add_argument('-t', '--threshold', type=float, default=DISTANCE_THRESHOLD,
                      help=f'Distance threshold in cm (default: {DISTANCE_THRESHOLD})')
    
    args = parser.parse_args()
    
    try:
        # Initialize stepper motor
        print("Initializing stepper motor...")
        setup()
        
        # Initialize ToF sensor
        print("Initializing VL53L0X distance sensor...")
        initialize_sensor()
        
        print(f"Rotating motor at {args.speed} RPM...")
        print(f"Motor will stop when an object is detected at {args.threshold}cm or closer")
        print("Press Ctrl+C to exit manually")
        
        # Main control loop
        while True:
            # Get distance reading in millimeters
            distance_mm = get_distance()
            # Convert to centimeters
            distance_cm = distance_mm / 10.0
            
            print(f"Distance: {distance_mm} mm ({distance_cm:.1f} cm)")
            
            # Check if distance is below threshold
            if distance_cm <= args.threshold:
                print(f"Object detected at {distance_cm:.1f}cm - stopping motor")
                break
            
            # Rotate motor by a small amount and then check distance again
            rotate_degrees(MOTOR_STEP_ANGLE, args.clockwise, args.speed)
            time.sleep(CHECK_INTERVAL)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup GPIO
        cleanup()
        print("GPIO pins cleaned up. Program terminated.")

if __name__ == "__main__":
    main()