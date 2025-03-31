#!/usr/bin/env python3
"""
Stepper Motor Control with TB6600 Driver on Raspberry Pi 4B
- GPIO 20: STEP (pulse) pin
- GPIO 21: DIR (direction) pin
"""

import RPi.GPIO as GPIO
import time
import sys

# Pin Definitions
STEP_PIN = 20  # GPIO 20 for step pulse
DIR_PIN = 21   # GPIO 21 for direction

# TB6600 Driver Settings
# Adjust these values based on your specific setup and requirements
PULSE_FREQUENCY = 1000  # Hz - Adjusts speed (1000 steps per second)
STEPS_PER_REVOLUTION = 1600  # Depends on your motor (usually 200 for 1.8° motors)
DIRECTION = 1  # 1 for clockwise, 0 for counterclockwise
MICROSTEP = 16  # Depends on TB6600 settings (1, 2, 4, 8, 16, or 32)

class StepperMotor:
    def __init__(self, step_pin, dir_pin):
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Initialize pins
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        
        # Set up pins as output
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        
        # Initialize pins to low
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.dir_pin, GPIO.LOW)
        
        # Set default parameters
        self.delay = 1.0 / (2 * PULSE_FREQUENCY)  # Delay between high and low states
    
    def set_direction(self, clockwise=True):
        """Set the direction of motor rotation"""
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
        time.sleep(0.01)  # Small delay for direction change to register
    
    def step(self, steps, clockwise=True):
        """Move the motor a specified number of steps"""
        # Set direction
        self.set_direction(clockwise)
        
        # Move the specified number of steps
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(self.delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.delay)
    
    def rotate_angle(self, angle, clockwise=True):
        """Rotate the motor by a specified angle in degrees"""
        steps = int((angle / 360) * STEPS_PER_REVOLUTION * MICROSTEP)
        self.step(steps, clockwise)
    
    def rotate_revolutions(self, revolutions, clockwise=True):
        """Rotate the motor by a specified number of revolutions"""
        steps = int(revolutions * STEPS_PER_REVOLUTION * MICROSTEP)
        self.step(steps, clockwise)
    
    def set_speed(self, rpm):
        """Set the motor speed in RPM (revolutions per minute)"""
        if rpm <= 0:
            raise ValueError("RPM must be greater than 0")
        
        # Calculate the delay based on RPM
        steps_per_second = (rpm * STEPS_PER_REVOLUTION * MICROSTEP) / 60
        self.delay = 1.0 / (2 * steps_per_second)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()

def main():
    try:
        # Create stepper motor instance
        motor = StepperMotor(STEP_PIN, DIR_PIN)
        
        # Set motor speed to 60 RPM
        motor.set_speed(60)
        
        print("Rotating motor clockwise for 1 revolution...")
        motor.rotate_revolutions(1, clockwise=True)
        
        time.sleep(1)  # Pause for 1 second
        
        print("Rotating motor counterclockwise for 180 degrees...")
        motor.rotate_angle(180, clockwise=False)
        
        time.sleep(1)  # Pause for 1 second
        
        # Demonstrate speed changes
        print("Rotating at different speeds...")
        motor.set_speed(30)  # Slow
        motor.rotate_angle(90, clockwise=True)
        
        motor.set_speed(120)  # Fast
        motor.rotate_angle(90, clockwise=True)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        # Clean up GPIO resources
        GPIO.cleanup()
        print("GPIO cleanup completed")

if __name__ == "__main__":
    main()