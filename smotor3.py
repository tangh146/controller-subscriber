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

# Start PWM with 0 duty cycle
servo.start(0)

# Function to convert angle to duty cycle
def angle_to_duty_cycle(angle):
    """Convert angle (0-180) to duty cycle (2.5-12.5)"""
    return 2.5 + (angle / 180.0) * 10.0

try:
    print("Starting servo test on GPIO 6, sweeping from 0° to 180°")
    print("Press Ctrl+C to stop")
    
    while True:
        # Sweep from 0 to 180 degrees
        print("Sweeping from 0° to 180°...")
        for angle in range(0, 181, 5):  # Step by 5 degrees for smoother movement
            duty_cycle = angle_to_duty_cycle(angle)
            servo.ChangeDutyCycle(duty_cycle)
            print(f"Current angle: {angle}°")
            time.sleep(0.1)  # Short delay to let servo move
        
        # Sweep from 180 to 0 degrees
        print("Sweeping from 180° to 0°...")
        for angle in range(180, -1, -5):  # Step by 5 degrees
            duty_cycle = angle_to_duty_cycle(angle)
            servo.ChangeDutyCycle(duty_cycle)
            print(f"Current angle: {angle}°")
            time.sleep(0.1)  # Short delay to let servo move

except KeyboardInterrupt:
    print("\nServo test stopped by user")
finally:
    # Clean up
    servo.stop()
    GPIO.cleanup()
    print("GPIO cleaned up")