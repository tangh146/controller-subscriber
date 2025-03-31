#!/usr/bin/env python3
"""
Stepper Motor Control Module for TB6600 Driver
- PUL+ connected to GPIO 21, PUL- to GND
- DIR+ connected to GPIO 20, DIR- to GND
"""

import RPi.GPIO as GPIO
import time

# GPIO pin configuration
PUL_PIN = 21  # Pulse pin
DIR_PIN = 20  # Direction pin
# ENA_PIN = 16  # Enable pin (uncomment if using)

# Motor configuration
# Using the driver's configured pulse/rev directly instead of calculating from steps and microstepping
TOTAL_STEPS = 6400  # TB6600 configured for 6400 pulses per revolution with 32 microstepping

def setup_stepper():
    """Initialize GPIO pins for stepper motor"""
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
    GPIO.output(DIR_PIN, GPIO.HIGH if direction else GPIO.LOW)
    
    # Calculate delay between pulses based on desired RPM
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

def dispense_product(revolutions=1, speed_rpm=10, clockwise=True):
    """
    Dispense a product by rotating the stepper motor
    
    Parameters:
    revolutions (int): Number of full revolutions to make
    speed_rpm (float): Speed in RPM
    clockwise (bool): Direction to rotate
    """
    try:
        degrees = 360 * revolutions
        print(f"Dispensing product: {revolutions} revolutions at {speed_rpm} RPM")
        rotate_degrees(degrees, clockwise, speed_rpm)
        print("Dispensing complete")
        return True
    except Exception as e:
        print(f"Error dispensing product: {e}")
        return False

def dispense_until_distance(target_distance_cm, max_steps=3200, speed_rpm=10, clockwise=True, get_distance_func=None):
    """
    Dispense a product by rotating the stepper motor until a target distance is detected
    
    Parameters:
    target_distance_cm (float): Target distance in centimeters to stop at
    max_steps (int): Maximum number of steps to prevent endless rotation
    speed_rpm (float): Speed in RPM
    clockwise (bool): Direction to rotate
    get_distance_func (function): Function to call to get the current distance
    
    Returns:
    bool: True if target distance was reached, False if max steps were hit
    """
    if get_distance_func is None:
        print("Error: No distance measurement function provided")
        return False
    
    # Convert target from cm to mm
    target_distance_mm = target_distance_cm * 10
    
    try:
        # Check initial distance reading
        initial_distance = get_distance_func()
        initial_distance_cm = initial_distance / 10.0
        print(f"Initial distance reading: {initial_distance_cm:.1f}cm")
        
        # If we're already detecting a very close distance at startup,
        # there might be a sensor issue - force the motor to move anyway
        force_movement = False
        if 0 < initial_distance < 100:  # Less than 10cm
            print(f"WARNING: Very close initial distance ({initial_distance_cm:.1f}cm) detected.")
            print("This may indicate a sensor error. Forcing motor movement.")
            force_movement = True
            # Take a few more readings to see if they're consistent
            readings = []
            for i in range(3):
                readings.append(get_distance_func())
                time.sleep(0.1)
            if all(r < 100 for r in readings if r > 0):
                print("Multiple suspicious readings confirmed. Sensor may need calibration.")
            
        # Set direction
        GPIO.output(DIR_PIN, GPIO.HIGH if clockwise else GPIO.LOW)
        
        # Calculate delay between pulses based on desired RPM
        delay = 60.0 / (speed_rpm * TOTAL_STEPS)
        pulse_duration = delay / 2  # Half the time high, half the time low
        
        print(f"Dispensing until distance {target_distance_cm}cm is reached (max steps: {max_steps})...")
        steps_taken = 0
        target_reached = False
        
        # Generate pulses until target distance is reached or max steps are taken
        # Force a minimum number of steps if we had a suspicious initial reading
        min_steps = 100 if force_movement else 0
        
        while steps_taken < max_steps:
            # Always move a minimum number of steps if forced
            if steps_taken < min_steps:
                must_continue = True
            else:
                must_continue = False
                
            # Check distance
            current_distance_mm = get_distance_func()
            current_distance_cm = current_distance_mm / 10.0
            
            # Print distance every 50 steps
            if steps_taken % 50 == 0 or steps_taken < 5:
                print(f"Current distance: {current_distance_cm:.1f}cm (Step {steps_taken})")
            
            # Check if target reached - but only after min_steps
            if not must_continue and current_distance_mm > 10 and current_distance_mm <= target_distance_mm:
                # Verify with additional readings
                confirmation_count = 1
                needed_confirmations = 3
                
                for _ in range(needed_confirmations - 1):
                    time.sleep(0.05)  # Short delay between readings
                    verify_distance = get_distance_func()
                    if verify_distance > 10 and verify_distance <= target_distance_mm:
                        confirmation_count += 1
                
                # Only consider target reached if we have enough confirmations
                if confirmation_count >= needed_confirmations:
                    print(f"Target distance confirmed: {current_distance_cm:.1f}cm after {steps_taken} steps")
                    target_reached = True
                    break
                else:
                    print(f"False positive detected. Continuing...")
            
            # If distance is invalid, retry
            if current_distance_mm <= 0:
                print("Invalid distance reading, retrying...")
                continue
            
            # Pulse the stepper
            GPIO.output(PUL_PIN, GPIO.HIGH)
            time.sleep(pulse_duration)
            GPIO.output(PUL_PIN, GPIO.LOW)
            time.sleep(pulse_duration)
            
            steps_taken += 1
        
        if not target_reached:
            print(f"Maximum steps reached ({max_steps}) without detecting target distance")
        
        return target_reached
    except Exception as e:
        print(f"Error dispensing product: {e}")
        return False

def cleanup_stepper():
    """Clean up GPIO pins for stepper motor"""
    GPIO.output(PUL_PIN, GPIO.LOW)
    # Don't call GPIO.cleanup() here as it might affect other GPIO usage
    # Just reset the pins we're using for the stepper
    print("Stepper motor pins reset")