#!/usr/bin/env python3
"""
Raspberry Pi Servo Controller Class
- Controls two servos with specific angle ranges:
  - Servo 1: 100 to 130 degrees
  - Servo 2: 0 to 180 degrees
"""

import RPi.GPIO as GPIO
import time

class ServoController:
    """
    Class to control two servo motors connected to a Raspberry Pi
    """
    
    def __init__(self, 
                 servo1_pin=6, 
                 servo2_pin=13, 
                 servo1_range=(60, 130), 
                 servo2_range=(0, 160),
                 pwm_freq=50):
        """
        Initialize the servo controller
        
        Args:
            servo1_pin: GPIO pin for servo 1 (BCM numbering)
            servo2_pin: GPIO pin for servo 2 (BCM numbering)
            servo1_range: Tuple of (min_angle, max_angle) for servo 1
            servo2_range: Tuple of (min_angle, max_angle) for servo 2
            pwm_freq: PWM frequency in Hz
        """
        # Save pin configuration
        self.SERVO1_PIN = servo1_pin
        self.SERVO2_PIN = servo2_pin
        
        # Save angle ranges
        self.SERVO1_MIN_ANGLE, self.SERVO1_MAX_ANGLE = servo1_range
        self.SERVO2_MIN_ANGLE, self.SERVO2_MAX_ANGLE = servo2_range
        
        # PWM frequency
        self.PWM_FREQ = pwm_freq
        
        # Initialize servos as None
        self.servo1 = None
        self.servo2 = None
        
        # Flag to track if setup has been called
        self.is_setup = False
    
    def setup(self):
        """
        Initialize GPIO and servo motors
        """
        if self.is_setup:
            return
            
        # Use GPIO numbering (not pin numbering)
        GPIO.setmode(GPIO.BCM)
        
        # Set up servo pins as outputs
        GPIO.setup(self.SERVO1_PIN, GPIO.OUT)
        GPIO.setup(self.SERVO2_PIN, GPIO.OUT)
        
        # Create PWM objects for each servo
        self.servo1 = GPIO.PWM(self.SERVO1_PIN, self.PWM_FREQ)
        self.servo2 = GPIO.PWM(self.SERVO2_PIN, self.PWM_FREQ)
        
        # Start PWM with servos at initial position
        self.servo1.start(self._angle_to_duty_cycle(self.SERVO1_MIN_ANGLE))
        self.servo2.start(self._angle_to_duty_cycle(self.SERVO2_MIN_ANGLE))
        
        self.is_setup = True
        return self
    
    def _angle_to_duty_cycle(self, angle):
        """
        Convert angle in degrees to duty cycle
        Most servos expect PWM duty cycle between 2.5% (0°) and 12.5% (180°)
        """
        return 2.5 + (angle / 180.0) * 10.0
    
    def set_servo1_angle(self, angle):
        """
        Set servo 1 to specified angle within allowed range
        """
        if not self.is_setup:
            self.setup()
            
        # Ensure angle is within specified limits
        angle = max(self.SERVO1_MIN_ANGLE, min(angle, self.SERVO1_MAX_ANGLE))
        
        # Convert angle to duty cycle and set servo
        duty_cycle = self._angle_to_duty_cycle(angle)
        self.servo1.ChangeDutyCycle(duty_cycle)
        
        # Small delay to allow servo to reach position
        time.sleep(0.1)
        return angle
    
    def set_servo2_angle(self, angle):
        """
        Set servo 2 to specified angle within allowed range
        """
        if not self.is_setup:
            self.setup()
            
        # Ensure angle is within specified limits
        angle = max(self.SERVO2_MIN_ANGLE, min(angle, self.SERVO2_MAX_ANGLE))
        
        # Convert angle to duty cycle and set servo
        duty_cycle = self._angle_to_duty_cycle(angle)
        self.servo2.ChangeDutyCycle(duty_cycle)
        
        # Small delay to allow servo to reach position
        time.sleep(0.1)
        return angle
    
    def sweep_servo1(self, start_angle=None, end_angle=None, step=1, delay=0.02):
        """
        Sweep servo 1 from start_angle to end_angle in steps
        If start_angle or end_angle is None, use the min/max values
        """
        if not self.is_setup:
            self.setup()
            
        if start_angle is None:
            start_angle = self.SERVO1_MIN_ANGLE
        if end_angle is None:
            end_angle = self.SERVO1_MAX_ANGLE
            
        # Ensure angles are within limits
        start_angle = max(self.SERVO1_MIN_ANGLE, min(start_angle, self.SERVO1_MAX_ANGLE))
        end_angle = max(self.SERVO1_MIN_ANGLE, min(end_angle, self.SERVO1_MAX_ANGLE))
        
        self._sweep_servo(self.servo1, start_angle, end_angle, step, delay)
    
    def sweep_servo2(self, start_angle=None, end_angle=None, step=1, delay=0.02):
        """
        Sweep servo 2 from start_angle to end_angle in steps
        If start_angle or end_angle is None, use the min/max values
        """
        if not self.is_setup:
            self.setup()
            
        if start_angle is None:
            start_angle = self.SERVO2_MIN_ANGLE
        if end_angle is None:
            end_angle = self.SERVO2_MAX_ANGLE
            
        # Ensure angles are within limits
        start_angle = max(self.SERVO2_MIN_ANGLE, min(start_angle, self.SERVO2_MAX_ANGLE))
        end_angle = max(self.SERVO2_MIN_ANGLE, min(end_angle, self.SERVO2_MAX_ANGLE))
        
        self._sweep_servo(self.servo2, start_angle, end_angle, step, delay)
    
    def _sweep_servo(self, servo, start_angle, end_angle, step=1, delay=0.02):
        """
        Sweep a servo from start_angle to end_angle in steps
        """
        if start_angle < end_angle:
            angles = range(start_angle, end_angle + 1, step)
        else:
            angles = range(start_angle, end_angle - 1, -step)
            
        for angle in angles:
            duty_cycle = self._angle_to_duty_cycle(angle)
            servo.ChangeDutyCycle(duty_cycle)
            time.sleep(delay)
    
    def cleanup(self):
        """
        Stop PWM and clean up GPIO resources
        """
        if self.is_setup:
            if self.servo1:
                self.servo1.stop()
            if self.servo2:
                self.servo2.stop()
            GPIO.cleanup()
            self.is_setup = False
    
    def run_demo(self):
        """
        Run a demonstration of the servos
        """
        try:
            if not self.is_setup:
                self.setup()
            print("Servos initialized")
            
            # Give servos time to initialize
            time.sleep(1)
            
            print(f"Sweeping Servo 1 ({self.SERVO1_MIN_ANGLE}° to {self.SERVO1_MAX_ANGLE}°)")
            self.sweep_servo1()
            time.sleep(0.5)
            
            print(f"Sweeping Servo 1 back ({self.SERVO1_MAX_ANGLE}° to {self.SERVO1_MIN_ANGLE}°)")
            self.sweep_servo1(self.SERVO1_MAX_ANGLE, self.SERVO1_MIN_ANGLE)
            time.sleep(0.5)
            
            print(f"Sweeping Servo 2 ({self.SERVO2_MIN_ANGLE}° to {self.SERVO2_MAX_ANGLE}°)")
            self.sweep_servo2()
            time.sleep(0.5)
            
            print(f"Sweeping Servo 2 back ({self.SERVO2_MAX_ANGLE}° to {self.SERVO2_MIN_ANGLE}°)")
            self.sweep_servo2(self.SERVO2_MAX_ANGLE, self.SERVO2_MIN_ANGLE)
            time.sleep(0.5)
            
            # Example of setting specific angles
            middle_angle1 = self.SERVO1_MIN_ANGLE + (self.SERVO1_MAX_ANGLE - self.SERVO1_MIN_ANGLE) // 2
            print(f"Setting Servo 1 to mid-position ({middle_angle1}°)")
            self.set_servo1_angle(middle_angle1)
            
            middle_angle2 = self.SERVO2_MIN_ANGLE + (self.SERVO2_MAX_ANGLE - self.SERVO2_MIN_ANGLE) // 2
            print(f"Setting Servo 2 to mid-position ({middle_angle2}°)")
            self.set_servo2_angle(middle_angle2)
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("Program stopped by user")
        finally:
            self.cleanup()
            print("Cleanup complete")

# Example usage when this file is run directly
if __name__ == "__main__":
    # Create a servo controller with default settings
    controller = ServoController()
    
    # Run the demo
    controller.run_demo()