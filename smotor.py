import RPi.GPIO as GPIO
import time

class TB6600StepperMotor:
    def __init__(self, pulse_pin, dir_pin, enable_pin=None, steps_per_rev=4800, microstepping=1):
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
        
        # Initialize the L298N motor controller as well
        self.l298n_motor = None
    
    def initialize_l298n_motor(self):
        """Initialize the L298N motor controller"""
        # Define pins for L298N motor controller
        ENABLE_PIN = 22  # PWM pin
        IN1_PIN = 23     # Direction control 1
        IN2_PIN = 24     # Direction control 2
        ENCODER_A_PIN = 17  # Encoder channel A
        ENCODER_B_PIN = 27  # Encoder channel B
        STEPS_PER_REV = 360  # Adjust based on your encoder's resolution
        
        # Create the L298N motor controller instance
        self.l298n_motor = L298NMotorController(ENABLE_PIN, IN1_PIN, IN2_PIN, 
                                               ENCODER_A_PIN, ENCODER_B_PIN, STEPS_PER_REV)
        return self.l298n_motor
        
    def move(self, l298n_rotation_angle=None):
        """
        Run the TB6600 stepper motor first, then the L298N motor if initialized.
        
        Args:
            l298n_rotation_angle (float, optional): The angle in degrees to rotate the L298N motor.
                                                    If None, the L298N motor will not rotate.
        """
        print("TB6600: Running stepper motor for 1 revolution slowly...")
        #self.rotate_revolutions(1, delay=0.001)
        
        #time.sleep(1)
        
        print("TB6600: Running stepper motor for 180 degrees quickly...")
        #self.rotate_degrees(180, delay=0.0003)
        
        #time.sleep(1)
        
        #print("TB6600: Running stepper motor for 1000 steps...")
        #self.step(1000, delay=0.0005)
        
        # If L298N motor is initialized and a rotation angle is provided, run it
        if self.l298n_motor is not None and l298n_rotation_angle is not None:
            time.sleep(1)
            print(f"L298N: Starting DC motor rotations for {l298n_rotation_angle} degrees...")
            
            # Perform rotations with the L298N motor
            for i in range(1):  # Reduced to 2 cycles for faster execution
                print(f"L298N: Rotation {i+1}: {l298n_rotation_angle} degrees clockwise")
                self.l298n_motor.rotate_degrees(l298n_rotation_angle, speed=60, clockwise=False)
                time.sleep(0.5)
                
                #print(f"L298N: Rotation {i+1}: {l298n_rotation_angle} degrees counter-clockwise")
                #self.l298n_motor.rotate_degrees(l298n_rotation_angle, speed=60, clockwise=False)
                #time.sleep(0.5)
    
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
        # Also clean up L298N motor if initialized
        if self.l298n_motor is not None:
            self.l298n_motor.cleanup()
        else:
            GPIO.cleanup()


class L298NMotorController:
    def __init__(self, enable_pin, in1_pin, in2_pin, encoder_a_pin, encoder_b_pin=None, steps_per_revolution=360):
        """
        Initialize L298N motor controller.
        
        Args:
            enable_pin: PWM pin for controlling motor speed
            in1_pin: Direction control pin 1
            in2_pin: Direction control pin 2
            encoder_a_pin: Encoder channel A pin
            encoder_b_pin: Encoder channel B pin (optional, for quadrature encoding)
            steps_per_revolution: Number of encoder steps per full revolution
        """
        self.enable_pin = enable_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.encoder_a_pin = encoder_a_pin
        self.encoder_b_pin = encoder_b_pin
        self.steps_per_revolution = steps_per_revolution
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
        
        # Setup PWM
        self.pwm = GPIO.PWM(self.enable_pin, 1000)  # 1000 Hz frequency
        self.pwm.start(0)  # Start with 0% duty cycle (motor stopped)
        
        # Setup encoder
        self.position = 0
        self.last_encoder_a = 0
        self.last_encoder_b = 0
        
        # Setup encoder pins (without edge detection)
        GPIO.setup(self.encoder_a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if self.encoder_b_pin:
            GPIO.setup(self.encoder_b_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def read_encoder(self):
        """
        Read encoder position using quadrature decoding with polling.
        """
        a_state = GPIO.input(self.encoder_a_pin)
        if self.encoder_b_pin is None:
            # Simple encoder (only channel A)
            if a_state == 1 and self.last_encoder_a == 0:  # Rising edge
                self.position += 1
            self.last_encoder_a = a_state
        else:
            b_state = GPIO.input(self.encoder_b_pin)
            current_state = (a_state << 1) | b_state
            prev_state = (self.last_encoder_a << 1) | self.last_encoder_b
            
            # Define valid transitions for quadrature decoding
            transition = (prev_state << 2) | current_state
            
            # Clockwise transitions (from datasheet or encoder spec)
            cw_transitions = {0b0001, 0b0111, 0b1110, 0b1000}
            # Counter-clockwise transitions
            ccw_transitions = {0b0010, 0b1011, 0b1101, 0b0100}
            
            if transition in cw_transitions:
                self.position += 1
            elif transition in ccw_transitions:
                self.position -= 1
            
            # Update previous states
            self.last_encoder_a = a_state
            self.last_encoder_b = b_state
    
    def set_direction(self, clockwise=True):
        """Set the direction of motor rotation"""
        if clockwise:
            GPIO.output(self.in1_pin, GPIO.HIGH)
            GPIO.output(self.in2_pin, GPIO.LOW)
        else:
            GPIO.output(self.in1_pin, GPIO.LOW)
            GPIO.output(self.in2_pin, GPIO.HIGH)
    
    def set_speed(self, speed):
        """Set the speed of the motor (0-100)"""
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100
        self.pwm.ChangeDutyCycle(speed)
    
    def stop(self):
        """Stop the motor"""
        self.pwm.ChangeDutyCycle(0)
        
    def cleanup(self):
        """Clean up GPIO pins"""
        self.pwm.stop()
        # Note: We don't call GPIO.cleanup() here to avoid conflicts with the TB6600 motor
    
    def rotate_degrees(self, degrees, speed=50, clockwise=True):
        """
        Rotate the motor by a specific number of degrees with timeout.
        """
        start_time = time.time()
        timeout = 5  # seconds (adjust based on expected max duration)
        
        # Calculate target position
        target_steps = int((degrees / 360) * self.steps_per_revolution)
        start_position = self.position
        target_position = start_position + target_steps if clockwise else start_position - target_steps
        
        # Start motor
        self.set_direction(clockwise)
        
        # Use PID-like approach for better precision
        max_speed = speed
        min_speed = 20  # Minimum speed to keep motor turning
        
        # Start with initial speed
        current_speed = max_speed
        self.set_speed(current_speed)
        
        # Wait until we've moved close to the desired position
        while True:
            if time.time() - start_time > timeout:
                print("Timeout reached. Stopping motor.")
                self.stop()
                break
            
            # Read encoder
            self.read_encoder()
            print(f"Current Pos: {self.position}, Target: {target_position}")
            
            # Calculate remaining distance
            remaining_steps = abs(target_position - self.position)
            
            # If we've reached target, stop
            if remaining_steps <= 1:
                print("Target reached. Stopping motor.")
                break
                
            # Slow down as we approach target for better precision
            if remaining_steps < target_steps * 0.2:  # Last 20% of movement
                # Gradual slowdown
                deceleration_factor = remaining_steps / (target_steps * 0.2)
                current_speed = max(min_speed, int(min_speed + (max_speed - min_speed) * deceleration_factor))
                self.set_speed(current_speed)
            
            # Check if we've gone too far (compensate for overshoot)
            if (clockwise and self.position > target_position) or (not clockwise and self.position < target_position):
                # Reverse direction briefly to correct
                print("Overshoot detected! Breaking the loop...")
                self.set_direction(not clockwise)
                self.set_speed(min_speed)
                time.sleep(0.05)
                self.set_direction(clockwise)
            
            time.sleep(0.001)  # Small delay to prevent CPU hogging
        
        # Stop motor
        self.stop()
        
        # Fine adjustment if needed (in case we overshot)
        if self.position != target_position:
            precise_adjustment = abs(self.position - target_position)
            if precise_adjustment <= 5:  # Small adjustment
                self.set_direction(self.position > target_position)
                self.set_speed(min_speed)
                while self.position != target_position:
                    self.read_encoder()
                    time.sleep(0.001)
                self.stop()
        
        return self.position - start_position  # Return actual steps moved


# Example usage
if __name__ == "__main__":
    try:
        # Define pins connected to TB6600
        PULSE_PIN = 20  # GPIO pin connected to PUL+
        DIR_PIN = 21    # GPIO pin connected to DIR+
        
        # Create stepper motor instance
        stepper_motor = TB6600StepperMotor(
            pulse_pin=PULSE_PIN,
            dir_pin=DIR_PIN,
            enable_pin=None,  # Not using the enable pin
            steps_per_rev=4800,
            microstepping=16
        )
        
        # Initialize and connect the L298N motor
        stepper_motor.initialize_l298n_motor()
        
        # Move both motors in sequence (TB6600 first, then L298N)
        # Specify the rotation angle for the L298N motor (e.g., 90 degrees)
        stepper_motor.move(l298n_rotation_angle=90)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        if 'stepper_motor' in locals():
            stepper_motor.cleanup()
