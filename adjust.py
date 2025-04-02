import rotary_encoder as rotary_encoder
import pigpio
import RPi.GPIO as GPIO
import time
import keyboard

class Worm:
    def __init__(self, enable_pin, in1_pin, in2_pin, encoder_a_pin, encoder_b_pin):
        # Pin setup
        self.enable_pin = enable_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.encoder_a_pin = encoder_a_pin
        self.encoder_b_pin = encoder_b_pin
        
        # Encoder tracking
        self.encoder_position = 0
        self.encoder_old_position = 0
        
        # Configure GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
        GPIO.setup(self.encoder_a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # PWM setup
        self.pwm = GPIO.PWM(self.enable_pin, 1000)
        self.pwm.start(0)
        
        self.pi = pigpio.pi()
        self.decoder = rotary_encoder.decoder(self.pi, self.encoder_a_pin, self.encoder_b_pin, lambda way: self.callback(way))

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

    def cleanup(self):
        """Clean up resources"""
        self.pwm.stop()
        GPIO.cleanup()
        
    def callback(self, way):
        self.encoder_position += way

if __name__ == "__main__":
    try:
        # Configuration - Update these to match your wiring!
        ENABLE_PIN = 22    # PWM pin (BCM numbering)
        IN1_PIN = 23       # Direction pin 1
        IN2_PIN = 24       # Direction pin 2
        ENCODER_A_PIN = 17 # Encoder channel A
        ENCODER_B_PIN = 27
        
        motor = Worm(ENABLE_PIN, IN1_PIN, IN2_PIN, ENCODER_A_PIN, ENCODER_B_PIN)
        
        print("Hold 'r' to rotate CCW. Press 'q' to quit.")
        motor_running = False
        
        while True:
            if keyboard.is_pressed('r'):
                if not motor_running:
                    motor.set_direction(ccw=True)
                    motor.set_speed(60)
                    motor_running = True
                    print("Rotating...")
            else:
                if motor_running:
                    motor.set_speed(0)
                    motor_running = False
                    print("Stopped.")
            if keyboard.is_pressed('q'):
                break
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        motor.cleanup()
