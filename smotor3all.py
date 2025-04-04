#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
import threading
import sys

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class ServoControl:
    def __init__(self):
        # Pin definitions (BCM numbering)
        self.GRABBER_PIN = 6      # GPIO 18 (PWM0)
        self.LEFT_RIGHT_PIN = 13   # GPIO 13 (PWM1)
        self.UP_DOWN_PIN1 = 19     # GPIO 12 (PWM0)
        self.UP_DOWN_PIN2 = 23     # GPIO 19 (PWM1)
        
        # Servo angle limits
        self.OPEN_GRABBER = 60
        self.CLOSE_GRABBER = 120
        
        self.OPEN_LEFT_RIGHT = 180
        self.CLOSE_LEFT_RIGHT = 0
        
        self.LOW_ANGLE = 130
        self.HIGH_ANGLE = 0
        self.current_pos = self.LOW_ANGLE
        
        # Speed control
        self.SPEED_DELAY = 0.05  # 50ms
        
        # Rest state definition
        self.rest_left_right = self.OPEN_LEFT_RIGHT  # Left
        self.rest_grabber = (self.OPEN_GRABBER + self.CLOSE_GRABBER) // 2  # Middle
        self.rest_up_down = self.HIGH_ANGLE  # Up position
        
        # Set up GPIO pins for servos
        GPIO.setup(self.GRABBER_PIN, GPIO.OUT)
        GPIO.setup(self.LEFT_RIGHT_PIN, GPIO.OUT)
        GPIO.setup(self.UP_DOWN_PIN1, GPIO.OUT)
        GPIO.setup(self.UP_DOWN_PIN2, GPIO.OUT)
        
        # Set up PWM for servos (50Hz is standard for servos)
        self.grabber_servo = GPIO.PWM(self.GRABBER_PIN, 50)
        self.left_right_servo = GPIO.PWM(self.LEFT_RIGHT_PIN, 50)
        self.up_down_servo1 = GPIO.PWM(self.UP_DOWN_PIN1, 50)
        self.up_down_servo2 = GPIO.PWM(self.UP_DOWN_PIN2, 50)
        
        # Start PWM
        self.grabber_servo.start(self._angle_to_duty_cycle(self.OPEN_GRABBER))
        self.left_right_servo.start(self._angle_to_duty_cycle(self.OPEN_LEFT_RIGHT))
        self.up_down_servo1.start(self._angle_to_duty_cycle(self.LOW_ANGLE))
        self.up_down_servo2.start(self._angle_to_duty_cycle(self.HIGH_ANGLE + self.LOW_ANGLE - self.LOW_ANGLE))
        
        # Initialize servos
        self.move_to_rest_state()
        
    def _angle_to_duty_cycle(self, angle):
        """Convert angle (0-180) to duty cycle (2.5-12.5)"""
        return 2.5 + (angle / 180.0) * 10.0
    
    def write_servo(self, servo, angle):
        """Write angle to servo"""
        servo.ChangeDutyCycle(self._angle_to_duty_cycle(angle))
        time.sleep(0.1)  # Small delay to let servo move
        
    def move_servo_smoothly(self, servo1, servo2, target):
        """Move two servos smoothly from current position to target"""
        step = 1 if target > self.current_pos else -1
        for i in range(self.current_pos, target + step, step):
            servo1.ChangeDutyCycle(self._angle_to_duty_cycle(i))
            servo2.ChangeDutyCycle(self._angle_to_duty_cycle(self.HIGH_ANGLE + self.LOW_ANGLE - i))
            time.sleep(self.SPEED_DELAY)
        self.current_pos = target
    
    def move_to_rest_state(self):
        """Move all servos to rest state"""
        print("Moving to rest state...")
        self.write_servo(self.left_right_servo, self.rest_left_right)
        self.write_servo(self.grabber_servo, self.rest_grabber)
        self.move_servo_smoothly(self.up_down_servo1, self.up_down_servo2, self.rest_up_down)
        print("Reached rest state.")
    
    def execute_pickup_sequence(self):
        """Execute pickup sequence"""
        print("Executing P1 sequence...")
        self.move_servo_smoothly(self.up_down_servo1, self.up_down_servo2, self.LOW_ANGLE)
        self.write_servo(self.grabber_servo, self.CLOSE_GRABBER)
        time.sleep(1)
        self.move_servo_smoothly(self.up_down_servo1, self.up_down_servo2, self.HIGH_ANGLE)
        self.write_servo(self.left_right_servo, self.CLOSE_LEFT_RIGHT)
        time.sleep(1)
        self.write_servo(self.grabber_servo, self.OPEN_GRABBER)
        self.move_to_rest_state()
        print("P1 sequence completed.")
    
    def redefine_rest_state(self):
        """Redefine rest state based on user input"""
        print("Enter new rest left/right position (0-180):")
        self.rest_left_right = self._read_angle()
        print("Enter new rest grabber position (0-180):")
        self.rest_grabber = self._read_angle()
        print("Enter new rest up/down position (0-180):")
        self.rest_up_down = self._read_angle()
        print("Rest state updated.")
    
    def _read_angle(self):
        """Read and validate angle from user input"""
        while True:
            try:
                angle = int(input())
                return max(0, min(180, angle))  # Constrain between 0-180
            except ValueError:
                print("Please enter a number between 0 and 180")
    
    def cleanup(self):
        """Clean up GPIO on exit"""
        self.grabber_servo.stop()
        self.left_right_servo.stop()
        self.up_down_servo1.stop()
        self.up_down_servo2.stop()
        GPIO.cleanup()

# Main function
def main():
    print("Servo control ready. Use commands:")
    print("O - Open Grabber, C - Close Grabber")
    print("L - Move Left, R - Move Right")
    print("U - Move Up, D - Move Down")
    print("P1 - Execute Pickup Sequence")
    print("S - Stop all movement, R4 - Redefine Rest State, R - Go to Rest State")
    print("Q - Quit program")
    
    servo_control = ServoControl()
    
    try:
        while True:
            command = input("Enter command: ").strip().upper()
            
            if command == "O":
                servo_control.write_servo(servo_control.grabber_servo, servo_control.OPEN_GRABBER)
            elif command == "C":
                servo_control.write_servo(servo_control.grabber_servo, servo_control.CLOSE_GRABBER)
            elif command == "L":
                servo_control.write_servo(servo_control.left_right_servo, servo_control.OPEN_LEFT_RIGHT)
            elif command == "R":
                servo_control.write_servo(servo_control.left_right_servo, servo_control.CLOSE_LEFT_RIGHT)
            elif command == "U":
                servo_control.move_servo_smoothly(servo_control.up_down_servo1, servo_control.up_down_servo2, servo_control.HIGH_ANGLE)
            elif command == "D":
                servo_control.move_servo_smoothly(servo_control.up_down_servo1, servo_control.up_down_servo2, servo_control.LOW_ANGLE)
            elif command == "P1":
                servo_control.move_to_rest_state()
                servo_control.execute_pickup_sequence()
            elif command == "R":
                servo_control.move_to_rest_state()
            elif command == "R4":
                servo_control.redefine_rest_state()
            elif command == "Q":
                break
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        servo_control.cleanup()
        print("GPIO cleaned up")

if __name__ == "__main__":
    main()