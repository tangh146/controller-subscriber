#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO

# Set up GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setwarnings(False)

# Configure GPIO 6 for servo
SERVO_PIN = 6
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Create PWM instance with 50Hz frequency (standard for servos)
servo = GPIO.PWM(SERVO_PIN, 50)

# Function to convert angle to duty cycle
def angle_to_duty_cycle(angle):
    """Convert angle (0-180) to duty cycle (2.5-12.5)"""
    return 2.5 + (angle / 180.0) * 10.0

try:
    # Start PWM at 0 degrees
    servo.start(angle_to_duty_cycle(0))
    print("Servo initialized at 0 degrees")
    time.sleep(0.5)
    
    current_angle = 0
    print("\nKeyboard Control:")
    print("Enter angle (0-180) or:")
    print("  +N : Increase angle by N degrees")
    print("  -N : Decrease angle by N degrees")
    print("  q  : Quit the program")
    
    while True:
        user_input = input("\nEnter command: ").strip().lower()
        
        if user_input == 'q':
            break
        
        try:
            if user_input.startswith('+'):
                # Increase angle
                increment = int(user_input[1:])
                new_angle = min(180, current_angle + increment)
            elif user_input.startswith('-'):
                # Decrease angle
                decrement = int(user_input[1:])
                new_angle = max(0, current_angle - decrement)
            else:
                # Direct angle input
                new_angle = int(user_input)
                
            # Validate angle range
            if 0 <= new_angle <= 180:
                print(f"Moving from {current_angle}° to {new_angle}°")
                servo.ChangeDutyCycle(angle_to_duty_cycle(new_angle))
                current_angle = new_angle
                time.sleep(0.3)  # Give servo time to move
                servo.ChangeDutyCycle(0)  # Stop the signal (reduces jitter)
            else:
                print("Angle must be between 0 and 180 degrees")
                
        except ValueError:
            print("Invalid input. Enter a number between 0-180, +N, -N, or q to quit")

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    # Clean up
    servo.stop()
    GPIO.cleanup()
    print("GPIO cleaned up")
