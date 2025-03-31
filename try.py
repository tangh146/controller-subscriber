import RPi.GPIO as GPIO
import time
import keyboard
import rotary_encoder
import pigpio
from time import sleep


class L298NMotorController:
    def __init__(self, enable_pin, in1_pin, in2_pin, steps_per_revolution=360):
        self.enable_pin = enable_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.steps_per_revolution = steps_per_revolution
        self.position = 0
        
        # Motor control setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
 
        # PWM setup
        self.pwm = GPIO.PWM(self.enable_pin, 1000)
        self.pwm.start(0)
        

    def set_direction(self, clockwise=True):
        if clockwise:
            GPIO.output(self.in1_pin, GPIO.HIGH)
            GPIO.output(self.in2_pin, GPIO.LOW)
        else:
            GPIO.output(self.in1_pin, GPIO.LOW)
            GPIO.output(self.in2_pin, GPIO.HIGH)

    def set_speed(self, speed):
        speed = max(0, min(100, speed))
        self.pwm.ChangeDutyCycle(speed)

    def rotate_degrees(self, degrees, speed=50, clockwise=True):
        target_steps = int((degrees / 360) * self.steps_per_revolution)
        start_position = self.position
        
        self.set_direction(clockwise)
        self.set_speed(speed)
        


    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    # Configuration - Update these values to match your wiring!
    ENABLE_PIN = 22   # PWM pin
    IN1_PIN = 23      # Direction control 1
    IN2_PIN = 24      # Direction control 2
    ENCODER_A_PIN = 17  # Encoder channel A
    ENCODER_B_PIN = 27  # Encoder channel B
    STEPS_PER_REV = 360  # Number of steps per full revolution
    
    ROTATE_DEGREES = 90  # Set desired rotation angle
    MOTOR_SPEED = 60     # Motor speed (0-100)
    
    position = 0 # The current position of the encoder - default to zero at program start.
    old_position = 0 # The previous position of the encoder - used to skip writing to the console
    # unless the position has changed.

    def callback(way): # Updates the position with the direction the encoder was turned.
        global position
        position += way

    pi = pigpio.pi() # Defines the specfic Raspberry Pi we are polling for information - defaults to the local device.
    

    try:
        motor = L298NMotorController(
            enable_pin=ENABLE_PIN,
            in1_pin=IN1_PIN,
            in2_pin=IN2_PIN,
            steps_per_revolution=STEPS_PER_REV
        )

        print(f"Press 'r' to rotate CCW by {ROTATE_DEGREES} degrees")
        print("Press 'q' to quit")

        while True:
            if keyboard.is_pressed('r'):
                print("\nRotating Counter-Clockwise...")
                motor.rotate_degrees(
                    degrees=ROTATE_DEGREES,
                    speed=MOTOR_SPEED,
                    clockwise=False
                )

                # Wait for key release
                while keyboard.is_pressed('r'):
                    decoder = rotary_encoder.decoder(pi, ENCODER_A_PIN, ENCODER_B_PIN, callback) # Creates an object that automatically fires
                    if position != old_position:
                        print("pos = {}".format(position))
                        old_position = position
                        sleep(0.001)
                        #time.sleep(0.1)
            elif keyboard.is_pressed('q'):
                print("\nExiting...")
                break
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        if 'motor' in locals():
            motor.cleanup()
