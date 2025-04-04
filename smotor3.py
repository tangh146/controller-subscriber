#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define the pin
PIN = 6

# Set up the pin as output
GPIO.setup(PIN, GPIO.OUT)

# Create PWM instance (if servo was connected to this pin)
servo = GPIO.PWM(PIN, 50)

try:
    # Start PWM at 0 duty cycle
    servo.start(0)
    print(f"GPIO pin {PIN} PWM reset to 0")
    
    # Stop PWM
    time.sleep(0.5)
    servo.stop()
    print(f"PWM stopped on GPIO pin {PIN}")
    
    # Set pin to LOW (0)
    GPIO.output(PIN, GPIO.LOW)
    print(f"GPIO pin {PIN} set to LOW (0)")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    # Clean up GPIO
    GPIO.cleanup()
    print("GPIO cleanup complete")