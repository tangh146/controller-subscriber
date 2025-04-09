import rotary_encoder as rotary_encoder
import pigpio
import RPi.GPIO as GPIO
import time
import keyboard

class Worm:
    def __init__(self, enable_pin, in1_pin, in2_pin, encoder_a_pin, encoder_b_pin):
        """
        Simplified L298N motor controller with basic encoder counting
        """
        # Pin setup
        self.enable_pin = enable_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.encoder_a_pin = encoder_a_pin
        self.encoder_b_pin = encoder_b_pin
        
        # Encoder tracking
        self.encoder_position = 0 # The current position of the encoder - default to zero at program start.
        self.encoder_old_position = 0 # The previous position of the encoder - used to skip writing to the console
        
        # Configure GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
        GPIO.setup(self.encoder_a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # PWM setup
        self.pwm = GPIO.PWM(self.enable_pin, 1000)
        self.pwm.start(0)
        
        self.pi = pigpio.pi() # Defines the specfic Raspberry Pi we are polling for information - defaults to the local device.
        self.decoder = rotary_encoder.decoder(self.pi, self.encoder_a_pin, self.encoder_b_pin, lambda way: self.callback(way)) # Creates an object that automatically fires

    def reset_encoder(self):
        """Reset the encoder counter"""
        self.encoder_position = 0
        self.encoder_old_position = 0

    def set_direction(self, ccw=True):
        """Set rotation direction (CCW by default)"""
        if ccw:
            GPIO.output(self.in1_pin, GPIO.LOW)
            GPIO.output(self.in2_pin, GPIO.HIGH)
        else:
            GPIO.output(self.in1_pin, GPIO.HIGH)
            GPIO.output(self.in2_pin, GPIO.LOW)

    def set_speed(self, speed):
        """Set motor speed (0-100)"""
        speed = max(0, min(100, speed))
        self.pwm.ChangeDutyCycle(speed)

    def rotate_degrees(self, target, speed=60):
        
        self.reset_encoder()
        self.set_direction(ccw=True)
        self.set_speed(speed)
        
        while (self.encoder_position < target): # Only prints the position of the encoder if a change has been made, refreshing every millisecond.
            # Helps reduce lag when moving a high resolution encoder extremely quickly.
            # Interstingly, the system didn't lose counts for me, but it did take an inordinate amount of time
            # to catch up when wiriting to the console.       
            if self.encoder_position != self.encoder_old_position:
                print("pos = {}".format(self.encoder_position))
                self.encoder_old_position = self.encoder_position
                time.sleep(0.001)
            
        self.set_speed(0)  # Stop motor

    def cleanup(self):
        """Clean up resources"""
        self.pwm.stop()
        GPIO.cleanup()
        
    def callback(self, way): # Updates the position with the direction the encoder was turned.
        self.encoder_position += way
