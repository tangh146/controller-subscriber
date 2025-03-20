import RPi.GPIO as GPIO
import time

class TB6600StepperMotor:
    def __init__(self, pulse_pin, dir_pin, enable_pin=None, steps_per_rev=200, microstepping=1):
        """
        Initialize the TB6600 stepper motor driver.
        
        Args:
            pulse_pin (int): GPIO pin connected to the PUL+ pin on TB6600
            dir_pin (int): GPIO pin connected to the DIR+ pin on TB6600
            enable_pin (int, optional): GPIO pin connected to the ENA+ pin on TB6600
            steps_per_rev (int): Number of steps per revolution (defaults to 200)
            microstepping (int): Microstepping setting on the TB6600 (1, 2, 4, 8, 16, or 32)
        """
        self.pulse_pin = pulse_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.steps_per_rev = steps_per_rev
        self.microstepping = microstepping
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pulse_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        
        # Set direction to a default value (clockwise in this case)
        GPIO.output(self.dir_pin, GPIO.HIGH)
        
        if self.enable_pin is not None:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            # Enable the driver (active low)
            GPIO.output(self.enable_pin, GPIO.LOW)
        
        print("Running motor for 1 revolution slowly...")
        self.rotate_revolutions(1, delay=0.001)
        
        time.sleep(1)
        
        print("Running motor for 180 degrees quickly...")
        self.rotate_degrees(180, delay=0.0003)
        
        time.sleep(1)
        
        print("Running motor for 1000 steps...")
        self.step(1000, delay=0.0005)
    
    def enable(self):
        """Enable the motor driver if an enable pin is connected."""
        if self.enable_pin is not None:
            GPIO.output(self.enable_pin, GPIO.LOW)
    
    def disable(self):
        """Disable the motor driver if an enable pin is connected."""
        if self.enable_pin is not None:
            GPIO.output(self.enable_pin, GPIO.HIGH)
    
    def step(self, steps, delay=0.0005):
        """
        Move the motor a specified number of steps.
        
        Args:
            steps (int): Number of steps to move
            delay (float): Delay between pulses in seconds (controls speed)
        """
        for _ in range(steps):
            GPIO.output(self.pulse_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.pulse_pin, GPIO.LOW)
            time.sleep(delay)
    
    def rotate_degrees(self, degrees, delay=0.0005):
        """
        Rotate the motor by a specified angle in degrees.
        
        Args:
            degrees (float): The angle to rotate in degrees
            delay (float): Delay between pulses in seconds (controls speed)
        """
        steps = int((degrees / 360.0) * self.steps_per_rev * self.microstepping)
        self.step(steps, delay)
    
    def rotate_revolutions(self, revolutions, delay=0.0005):
        """
        Rotate the motor by a specified number of revolutions.
        
        Args:
            revolutions (float): The number of revolutions to rotate
            delay (float): Delay between pulses in seconds (controls speed)
        """
        steps = int(revolutions * self.steps_per_rev * self.microstepping)
        self.step(steps, delay)
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if self.enable_pin is not None:
            self.disable()
        GPIO.cleanup()


# Example usage
if __name__ == "__main__":
    try:
        # Define pins connected to TB6600
        PULSE_PIN = 20  # GPIO pin connected to PUL+
        DIR_PIN = 21    # GPIO pin connected to DIR+
        
        # Create stepper motor instance (adjust parameters as needed)
        # Common values for steps_per_rev: 200 (1.8° motor) or 400 (0.9° motor)
        # Set microstepping according to your TB6600 switch settings (1, 2, 4, 8, 16, 32)
        motor = TB6600StepperMotor(
            pulse_pin=PULSE_PIN,
            dir_pin=DIR_PIN,
            enable_pin=None,  # Not using the enable pin
            steps_per_rev=200,
            microstepping=16
        )
        
        print("Running motor for 1 revolution slowly...")
        motor.rotate_revolutions(1, delay=0.001)
        
        time.sleep(1)
        
        print("Running motor for 180 degrees quickly...")
        motor.rotate_degrees(180, delay=0.0003)
        
        time.sleep(1)
        
        print("Running motor for 1000 steps...")
        motor.step(1000, delay=0.0005)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        if 'motor' in locals():
            motor.cleanup()