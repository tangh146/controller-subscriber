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

if __name__ == "__main__":
    try:
        # Configuration - Update these to match your wiring!
        ENABLE_PIN = 22    # PWM pin (BCM numbering)
        IN1_PIN = 23       # Direction pin 1
        IN2_PIN = 24       # Direction pin 2
        ENCODER_A_PIN = 17 # Encoder channel A
        ENCODER_B_PIN = 27
        ROTATION_DEGREES = 3600  # Default rotation angle
        
        motor = Worm(ENABLE_PIN, IN1_PIN, IN2_PIN, ENCODER_A_PIN, ENCODER_B_PIN)
        
        print(f"Press 'r' to rotate {ROTATION_DEGREES}° CCW")
        print("Press 'q' to quit")
        
        while True:
            if keyboard.is_pressed('r'):
                print("Rotating...")
                motor.rotate_degrees(ROTATION_DEGREES)
                print("Rotation complete")
                # Wait for key release
                while keyboard.is_pressed('r'):
                    time.sleep(0.1)
            elif keyboard.is_pressed('q'):
                break
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        motor.cleanup()
