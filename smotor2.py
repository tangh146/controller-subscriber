#!/usr/bin/env python3
"""
Raspberry Pi 4B Stepper Motor Control with TB6600 Driver
- PUL+ connected to GPIO 21, PUL- to GND
- DIR+ connected to GPIO 20, DIR- to GND
"""

import RPi.GPIO as GPIO
import time
import argparse

# GPIO pin configuration
PUL_PIN = 21  # Pulse pin
DIR_PIN = 20  # Direction pin
# ENA_PIN = 16  # Enable pin (uncomment if using)

# Motor configuration (adjust these based on your motor and application)
STEPS_PER_REVOLUTION = 6400  # Standard for many stepper motors (1.8° per step)
MICROSTEP_FACTOR = 32  # Microstep setting on your TB6600 (1, 2, 4, 8, 16, or 32)
TOTAL_STEPS = STEPS_PER_REVOLUTION * MICROSTEP_FACTOR  # Steps for a full revolution

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup pin modes
    GPIO.setup(PUL_PIN, GPIO.OUT)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    # GPIO.setup(ENA_PIN, GPIO.OUT)  # Uncomment if using ENA
    
    # Initial states
    GPIO.output(PUL_PIN, GPIO.LOW)
    GPIO.output(DIR_PIN, GPIO.LOW)
    # GPIO.output(ENA_PIN, GPIO.LOW)  # Uncomment if using ENA (LOW = enabled)

def rotate_motor(direction, steps, speed_rpm):
    """
    Rotate the stepper motor
    
    Parameters:
    direction (bool): True for clockwise, False for counterclockwise
    steps (int): Number of steps to rotate
    speed_rpm (float): Motor speed in RPM
    """
    # Set direction
    GPIO.output(DIR_PIN, GPIO.LOW if direction else GPIO.HIGH)
    
    # Calculate delay between pulses based on desired RPM
    # delay = 60 / (speed_rpm * TOTAL_STEPS * 2)
    delay = 60.0 / (speed_rpm * TOTAL_STEPS)
    pulse_duration = delay / 2  # Half the time high, half the time low
    
    # Generate pulses
    for _ in range(steps):
        GPIO.output(PUL_PIN, GPIO.HIGH)
        time.sleep(pulse_duration)
        GPIO.output(PUL_PIN, GPIO.LOW)
        time.sleep(pulse_duration)

def rotate_degrees(degrees, direction, speed_rpm):
    """
    Rotate the motor by a specific angle in degrees
    
    Parameters:
    degrees (float): Angle to rotate in degrees
    direction (bool): True for clockwise, False for counterclockwise
    speed_rpm (float): Motor speed in RPM
    """
    steps = int((degrees / 360.0) * TOTAL_STEPS)
    rotate_motor(direction, steps, speed_rpm)

def cleanup():
    """Clean up GPIO pins"""
    GPIO.output(PUL_PIN, GPIO.LOW)
    # GPIO.output(ENA_PIN, GPIO.HIGH)  # Uncomment if using ENA (HIGH = disabled)
    GPIO.cleanup()

def main():
    """Main function to parse arguments and control motor"""
    parser = argparse.ArgumentParser(description='Control a stepper motor with TB6600 driver')
    
    # Add arguments
    parser.add_argument('-d', '--degrees', type=float, default=360.0,
                      help='Angle to rotate in degrees (default: 360)')
    parser.add_argument('-s', '--speed', type=float, default=10.0,
                      help='Motor speed in RPM (default: 10)')
    parser.add_argument('-c', '--clockwise', action='store_true',
                      help='Rotate clockwise (default: counterclockwise)')
    parser.add_argument('-r', '--revolutions', type=int, default=1,
                      help='Number of full revolutions (default: 1)')
    parser.add_argument('-t', '--continuous', action='store_true',
                      help='Run continuously until Ctrl+C is pressed')
    
    args = parser.parse_args()
    
    try:
        setup()
        print(f"Motor configured with {STEPS_PER_REVOLUTION} steps per revolution and {MICROSTEP_FACTOR}x microstepping")
        print(f"Direction: {'Clockwise' if args.clockwise else 'Counterclockwise'}")
        
        if args.continuous:
            print("Running continuously. Press Ctrl+C to stop...")
            try:
                while True:
                    rotate_degrees(360, args.clockwise, args.speed)
            except KeyboardInterrupt:
                print("\nStopping motor...")
        else:
            total_degrees = args.degrees * args.revolutions
            print(f"Rotating {total_degrees} degrees at {args.speed} RPM...")
            rotate_degrees(total_degrees, args.clockwise, args.speed)
            print("Rotation complete.")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup()
        print("GPIO pins cleaned up.")

if __name__ == "__main__":
    main()