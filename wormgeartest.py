import RPi.GPIO as GPIO
import time
import keyboard  # Requires 'keyboard' library (install with pip)

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
        GPIO.cleanup()

    def rotate_degrees(self, degrees, speed=50, clockwise=True):
        """
        Rotate the motor by a specific number of degrees with timeout.
        """
        start_time = time.time()
        timeout = 1000  # seconds (adjust based on expected max duration)
        
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


if __name__ == "__main__":
    try:
        # Configuration - Update these values to match your wiring!
        ENABLE_PIN = 22   # PWM pin
        IN1_PIN = 23      # Direction control 1
        IN2_PIN = 24      # Direction control 2
        ENCODER_A_PIN = 17  # Encoder channel A
        ENCODER_B_PIN = 27  # Encoder channel B
        STEPS_PER_REV = 360  # Adjust based on your encoder's resolution
        
        rotate_degrees = 1000  # Set desired rotation angle
        motor_speed = 60     # Set motor speed (0-100)

        # Initialize motor controller
        motor = L298NMotorController(
            enable_pin=ENABLE_PIN,
            in1_pin=IN1_PIN,
            in2_pin=IN2_PIN,
            encoder_a_pin=ENCODER_A_PIN,
            encoder_b_pin=ENCODER_B_PIN,
            steps_per_revolution=STEPS_PER_REV
        )

        print(f"Press 'r' to rotate CCW by {rotate_degrees} degrees")
        print("Press 'q' to quit")

        while True:
            if keyboard.is_pressed('r'):
                print("\nRotating Counter-Clockwise...")
                motor.rotate_degrees(
                    degrees=rotate_degrees,
                    speed=motor_speed,
                    clockwise=False  # CCW rotation
                )
                # Wait for key release
                while keyboard.is_pressed('r'):
                    time.sleep(0.1)
            elif keyboard.is_pressed('q'):
                print("\nExiting...")
                break
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        if 'motor' in locals():
            motor.cleanup()
