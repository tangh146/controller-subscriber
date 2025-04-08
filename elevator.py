#!/usr/bin/env python3
"""
Integrated Raspberry Pi Stepper Motor Control with VL53L0X Distance Sensor and Servo Sequence
- Controls a stepper motor via TB6600 driver (DIR+/PUL+)
- Rotates clockwise until VL53L0X detects distance > 20cm
- Then runs a servo sequence instead of waiting
- After servo sequence, returns to initial position by rotating counterclockwise
- Uses smbus2 for I2C communication with VL53L0X
"""

import RPi.GPIO as GPIO
import time
from smbus2 import SMBus
from smotor3all import ServoController  # Import ServoController class

# Pin definitions
DIR_PIN = 20    # Direction pin (DIR+)
PUL_PIN = 21    # Pulse pin (PUL+)
DISTANCE_THRESHOLD = 608  # 20cm in mm

# VL53L0X parameters
VL53L0X_ADDR = 0x29
VL53L0X_REG_ID = 0xC0
VL53L0X_REG_SYSRANGE_START = 0x00
VL53L0X_REG_RESULT_RANGE_STATUS = 0x14
I2C_BUS = 1  # Raspberry Pi 4B uses I2C bus 1

# Motor parameters
STEP_DELAY = 0.0001  # Adjust for desired speed
FORWARD_DIRECTION = 1  # 1 for clockwise, 0 for counterclockwise
REVERSE_DIRECTION = 0  # Opposite of FORWARD_DIRECTION
MICROSTEP_FACTOR = 16  # 32 microsteps per full step
FULL_STEPS_PER_REV = 200  # Standard for NEMA stepper motors (1.8° per step)
STEPS_PER_REV = FULL_STEPS_PER_REV * MICROSTEP_FACTOR  # 6400 pulses per revolution

# Initialize GPIO
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(PUL_PIN, GPIO.OUT)
    GPIO.output(DIR_PIN, FORWARD_DIRECTION)
    print("GPIO initialized")

# Initialize VL53L0X sensor
def setup_sensor():
    bus = SMBus(I2C_BUS)
    
    # Check if sensor is present
    try:
        sensor_id = bus.read_byte_data(VL53L0X_ADDR, VL53L0X_REG_ID)
        if sensor_id == 0xEE:
            print("VL53L0X sensor found")
        else:
            print(f"Unexpected sensor ID: 0x{sensor_id:02X}")
    except Exception as e:
        print(f"Error communicating with sensor: {e}")
        return None
    
    # Initialize sensor (simplified initialization)
    # For a real application, the init sequence should follow the VL53L0X datasheet
    # This is a basic initialization
    
    print("VL53L0X sensor initialized")
    return bus

# Read distance from VL53L0X (mm)
def read_distance(bus):
    try:
        # Start single range measurement
        bus.write_byte_data(VL53L0X_ADDR, VL53L0X_REG_SYSRANGE_START, 0x01)
        
        # Wait for measurement completion
        range_status = 0
        while (range_status & 0x01) == 0:
            range_status = bus.read_byte_data(VL53L0X_ADDR, VL53L0X_REG_RESULT_RANGE_STATUS)
            time.sleep(0.01)
        
        # Read distance value (2 bytes)
        high_byte = bus.read_byte_data(VL53L0X_ADDR, VL53L0X_REG_RESULT_RANGE_STATUS + 10)
        low_byte = bus.read_byte_data(VL53L0X_ADDR, VL53L0X_REG_RESULT_RANGE_STATUS + 11)
        
        # Combine bytes to get distance in mm
        distance = (high_byte << 8) | low_byte
        return distance
    except Exception as e:
        print(f"Error reading distance: {e}")
        return 0

# Function to rotate stepper motor
def step_motor(steps, direction):
    # Set direction - make sure the direction change is applied
    print(f"Setting direction pin to {'clockwise' if direction == FORWARD_DIRECTION else 'counterclockwise'}")
    GPIO.output(DIR_PIN, direction)
    time.sleep(0.01)  # Small delay to ensure direction change is registered
    
    for _ in range(steps):
        GPIO.output(PUL_PIN, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(PUL_PIN, GPIO.LOW)
        time.sleep(STEP_DELAY)

# Function to run servo sequence
def run_servo_sequence_partial():
    """Run steps 1-8 of the servo sequence (excluding the final step)"""
    print("Running partial servo sequence (steps 1-8)...")
    
    # Create an instance of ServoController
    servo_controller = ServoController()
    
    steps = [
        (1, "Setting initial positions (Servo 1: 0°, Servo 2: 45°, Servo 3: 165°)", 
         [(0, 0), (1, 45), (2, 165)]),
        (2, "Moving Servo 1 to 90°", [(0, 90)]),
        (3, "Moving Servo 1 to 180°", [(0, 180)]),
        (4, "Moving Servo 2 to 130°", [(1, 130)]),
        (5, "Moving Servo 3 to 180°", [(2, 180)]),
        (6, "Moving Servo 2 to 45°", [(1, 45)]),
        (7, "Moving Servo 1 to 90°", [(0, 90)]),
        (8, "Moving Servo 1 to 0°", [(0, 0)])
        # Step 9 is excluded and will be run separately
    ]
    
    try:
        for step_num, description, movements in steps:
            print(f"Step {step_num}: {description}")
            
            for servo_idx, angle in movements:
                servo_controller.set_angle(servo_idx, angle)
            
            time.sleep(1)  # Wait between steps
        
        print("Partial servo sequence completed (steps 1-8)!")
        
        # Return the controller so we can use it again later
        return servo_controller
        
    except Exception as e:
        print(f"Error during servo sequence: {e}")
        # Still return the controller even if an error occurred
        return servo_controller

def run_servo_final_step(servo_controller):
    """Run only the final step (step 9) of the servo sequence"""
    print("Running final servo step (Step 9: Moving Servo 3 to 165°)...")
    
    try:
        # Execute only step 9
        servo_controller.set_angle(2, 165)  # Move Servo 3 to 165°
        time.sleep(0.5)  # Allow time for servo to reach position
        print("Final servo step completed!")
    except Exception as e:
        print(f"Error during final servo step: {e}")
    finally:
        # Only stop the servos but don't do GPIO.cleanup()
        for servo in servo_controller.servos:
            servo.stop()
        
    print("Servo sequence fully completed")

# Main function

def run_elevator_with_servo():
    print("Starting integrated elevator and servo control")
    try:
        # Setup
        setup_gpio()
        bus = setup_sensor()
        
        if bus is None:
            print("Failed to initialize sensor. Exiting.")
            return
        
        print("Starting motor rotation...")
        print("Will stop when distance exceeds 20cm, run servo sequence, then return to initial position")
        
        total_steps = 0  # Track total steps taken
        step_increment = 500  # Number of steps to take before checking distance
        
        # Step forward until distance threshold is exceeded
        while True:
            # Get distance reading in mm
            distance = read_distance(bus)
            print(f"Distance: {distance} mm")
            
            if distance > DISTANCE_THRESHOLD:
                print(f"Distance threshold exceeded ({distance} mm > {DISTANCE_THRESHOLD} mm)")
                print("Stopping forward movement")
                break
            
            # Rotate motor forward
            step_motor(step_increment, FORWARD_DIRECTION)
            total_steps += step_increment
            
        # Change direction for return journey
        print(f"Changing direction from {FORWARD_DIRECTION} to {REVERSE_DIRECTION}")
        GPIO.output(DIR_PIN, REVERSE_DIRECTION)
        
        # Run steps 1-8 of the servo sequence (excluding the final step)
        print("Starting partial servo sequence (steps 1-8) instead of waiting 10 seconds")
        servo_controller = run_servo_sequence_partial()
        
        # Return to initial position by stepping in reverse direction
        print(f"Returning to initial position (steps to reverse: {total_steps})")
        step_motor(total_steps, REVERSE_DIRECTION)
        print("Returned to initial position.")
        
        # Now run only the final step of the servo sequence
        print("Running final servo step (step 9) after returning to initial position")
        run_servo_final_step(servo_controller)
        
        print("Integrated sequence completed successfully.")
            
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        GPIO.cleanup()
        if 'bus' in locals() and bus is not None:
            bus.close()
        print("GPIO and I2C cleaned up")

if __name__ == "__main__":
    run_elevator_with_servo()
