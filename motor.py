import RPi.GPIO as GPIO
import time

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
        
        # Setup encoder pins
        GPIO.setup(self.encoder_a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.encoder_a_pin, GPIO.BOTH, callback=self._encoder_callback)
        
        if self.encoder_b_pin:
            # Setup quadrature encoding for direction detection
            GPIO.setup(self.encoder_b_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.encoder_b_pin, GPIO.BOTH, callback=self._encoder_b_callback)
    
    def _encoder_callback(self, channel):
        """Callback for encoder channel A pulses, updates position"""
        a_state = GPIO.input(self.encoder_a_pin)
        
        if self.encoder_b_pin:
            # Quadrature encoding for direction detection
            b_state = GPIO.input(self.encoder_b_pin)
            
            # Determine direction based on the state of both channels
            if a_state != self.last_encoder_a:
                # If A changed
                if a_state == 1:  # Rising edge on A
                    if b_state == 0:  # B is low
                        self.position += 1
                    else:  # B is high
                        self.position -= 1
                else:  # Falling edge on A
                    if b_state == 1:  # B is high
                        self.position += 1
                    else:  # B is low
                        self.position -= 1
            
            self.last_encoder_a = a_state
        else:
            # Simple encoder (no direction detection)
            if a_state == 1 and self.last_encoder_a == 0:  # Rising edge
                self.position += 1
            
            self.last_encoder_a = a_state
    
    def _encoder_b_callback(self, channel):
        """Callback for encoder channel B pulses, used for direction detection"""
        # Store the state for use in channel A callback
        self.last_encoder_b = GPIO.input(self.encoder_b_pin)
    
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
        Rotate the motor by a specific number of degrees
        
        Args:
            degrees: Number of degrees to rotate
            speed: Motor speed (0-100)
            clockwise: Direction of rotation
        """
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
            # Calculate remaining distance
            remaining_steps = abs(target_position - self.position)
            
            # If we've reached target, stop
            if remaining_steps <= 1:
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
                self.set_direction(not clockwise)
                self.set_speed(min_speed)
                time.sleep(0.05)
                self.set_direction(clockwise)
            
            time.sleep(0.01)  # Small delay to prevent CPU hogging
        
        # Stop motor
        self.stop()
        
        # Fine adjustment if needed (in case we overshot)
        if self.position != target_position:
            precise_adjustment = abs(self.position - target_position)
            if precise_adjustment <= 5:  # Small adjustment
                self.set_direction(self.position > target_position)
                self.set_speed(min_speed)
                time.sleep(0.05)
                self.stop()
        
        return self.position - start_position  # Return actual steps moved


def main():
    # Define pins - adjust these to match your wiring
    ENABLE_PIN = 18  # PWM pin
    IN1_PIN = 23     # Direction control 1
    IN2_PIN = 24     # Direction control 2
    ENCODER_A_PIN = 17  # Encoder channel A
    ENCODER_B_PIN = 27  # Encoder channel B (for direction detection)
    STEPS_PER_REV = 360  # Adjust based on your encoder's resolution
    
    # Setup the motor controller with encoder
    motor = L298NMotorController(ENABLE_PIN, IN1_PIN, IN2_PIN, ENCODER_A_PIN, ENCODER_B_PIN, STEPS_PER_REV)
    
    try:
        print("Starting motor control program")
        
        # Calibration step to determine actual steps per 60 degrees
        print("Calibrating encoder steps per 60 degrees...")
        motor.set_direction(True)
        motor.set_speed(50)
        start_pos = motor.position
        time.sleep(2)  # Run for 2 seconds
        motor.stop()
        total_steps = motor.position - start_pos
        time.sleep(1)
        
        # Calculate estimated steps for 60 degrees based on measured rotation
        # This assumes the motor did approximately one full rotation in 2 seconds
        estimated_rotation = 360  # degrees (assumption)
        steps_per_degree = total_steps / estimated_rotation
        steps_per_60_degrees = steps_per_degree * 60
        
        print(f"Calibration complete. Estimated steps per 60 degrees: {steps_per_60_degrees:.1f}")
        
        # Reset position counter
        motor.position = 0
        
        # Perform precise 60-degree rotations
        for i in range(5):
            print(f"Rotation {i+1}: 60 degrees clockwise")
            actual_steps = motor.rotate_degrees(60, speed=60, clockwise=True)
            print(f"Moved {actual_steps} steps")
            time.sleep(1)  # Pause between rotations
            
            print(f"Rotation {i+1}: 60 degrees counter-clockwise")
            actual_steps = motor.rotate_degrees(60, speed=60, clockwise=False)
            print(f"Moved {actual_steps} steps")
            time.sleep(1)  # Pause between rotations
    
    except KeyboardInterrupt:
        print("Program stopped by user")
        
    finally:
        # Clean up
        motor.cleanup()
        print("Motor control program finished")


if __name__ == "__main__":
    main()