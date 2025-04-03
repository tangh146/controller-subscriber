#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# GPIO pins configuration
DIR_PIN = 20    # Direction pin
STEP_PIN = 21   # Step pin

# Motor configuration
STEPS_PER_REVOLUTION = 200  # Standard for many stepper motors (1.8° per step)
                            # Adjust based on your specific motor
                            
MICROSTEPS = 32             # Microstep setting on TB6600 (1, 2, 4, 8, 16, or 32)
                           # Adjust based on your TB6600 switch settings
                           
ACTUAL_STEPS = STEPS_PER_REVOLUTION * MICROSTEPS

# Time between steps (seconds)
STEP_DELAY = 0.001         # Adjust for desired speed

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False)

# Setup pins as outputs
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

def rotate_stepper(revolutions, direction):
    """
    Rotate the stepper motor the specified number of revolutions
    in the given direction (True for clockwise, False for counterclockwise)
    """
    # Set direction
    GPIO.output(DIR_PIN, GPIO.HIGH if direction else GPIO.LOW)
    
    # Calculate total steps needed
    steps = int(revolutions * ACTUAL_STEPS)
    
    print(f"Rotating {'clockwise' if direction else 'counterclockwise'} for {revolutions} revolutions ({steps} steps)")
    
    # Execute steps
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(STEP_DELAY)
    
    print("Rotation complete")

try:
    # 5 revolutions clockwise
    rotate_stepper(5, True)
    
    # Short pause between direction changes
    time.sleep(0.5)
    
    # 5 revolutions counterclockwise
    rotate_stepper(5, False)
    
    print("Motion sequence complete")
    
except KeyboardInterrupt:
    print("Program stopped by user")
    
finally:    
    # Cleanup GPIO
    GPIO.cleanup()
    print("GPIO cleaned up")