import RPi.GPIO as GPIO
from time import sleep

def setup_motor(in1=24, in2=23, en=25):
    """
    Setup the motor with the specified GPIO pins.
    
    Args:
        in1 (int): GPIO pin for input 1
        in2 (int): GPIO pin for input 2
        en (int): GPIO pin for enable
        
    Returns:
        tuple: (PWM object, initial direction)
    """
    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en, GPIO.OUT)
    
    # Set initial state
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    
    # Setup PWM
    p = GPIO.PWM(en, 1000)
    p.start(25)  # Start with 25% duty cycle
    
    # Initial direction (1=forward, 0=backward)
    temp1 = 1
    
    return p, temp1

def motor_control(in1=24, in2=23, en=25):
    """
    Control a DC motor using PWM.
    
    Args:
        in1 (int): GPIO pin for input 1
        in2 (int): GPIO pin for input 2
        en (int): GPIO pin for enable
    """
    p, temp1 = setup_motor(in1, in2, en)
    
    print("\n")
    print("The default speed & direction of motor is LOW & Forward.....")
    print("r-run s-stop f-forward b-backward l-low m-medium h-high e-exit")
    print("\n")
    
    while True:
        try:
            x = input()  # Using input() instead of raw_input() for Python 3 compatibility
        except NameError:
            # Fall back to raw_input() for Python 2
            x = raw_input()
            
        if x == 'r':
            print("run")
            if temp1 == 1:
                GPIO.output(in1, GPIO.HIGH)
                GPIO.output(in2, GPIO.LOW)
                print("forward")
            else:
                GPIO.output(in1, GPIO.LOW)
                GPIO.output(in2, GPIO.HIGH)
                print("backward")
                
        elif x == 's':
            print("stop")
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)
            
        elif x == 'f':
            print("forward")
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
            temp1 = 1
            
        elif x == 'b':
            print("backward")
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
            temp1 = 0
            
        elif x == 'l':
            print("low")
            p.ChangeDutyCycle(25)
            
        elif x == 'm':
            print("medium")
            p.ChangeDutyCycle(50)
            
        elif x == 'h':
            print("high")
            p.ChangeDutyCycle(75)
            
        elif x == 'e':
            GPIO.cleanup()
            break
            
        else:
            print("<<< wrong data >>>")
            print("please enter the defined data to continue.....")

# Create a Motor class for more flexible use
class Motor:
    def __init__(self, in1=24, in2=23, en=25, encoder_a=17, encoder_b=27):
        """
        Initialize a motor controller with encoder feedback.
        
        Args:
            in1 (int): GPIO pin for input 1
            in2 (int): GPIO pin for input 2
            en (int): GPIO pin for enable
            encoder_a (int): GPIO pin for encoder channel A
            encoder_b (int): GPIO pin for encoder channel B
        """
        self.in1 = in1
        self.in2 = in2
        self.en = en
        self.encoder_a = encoder_a
        self.encoder_b = encoder_b
        self.direction = 1  # 1=forward, 0=backward
        self.pulse_count = 0
        self.last_encoder_a = 0
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(in1, GPIO.OUT)
        GPIO.setup(in2, GPIO.OUT)
        GPIO.setup(en, GPIO.OUT)
        
        # Setup encoder pins as inputs with pull-up resistors
        GPIO.setup(encoder_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(encoder_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Add event detection for encoder
        GPIO.add_event_detect(encoder_a, GPIO.BOTH, callback=self._encoder_callback)
        
        # Set initial state
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        
        # Setup PWM
        self.pwm = GPIO.PWM(en, 1000)
        self.pwm.start(25)  # Start with 25% duty cycle
    
    def forward(self):
        """Set motor to move forward."""
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        self.direction = 1
        return "forward"
    
    def backward(self):
        """Set motor to move backward."""
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        self.direction = 0
        return "backward"
    
    def stop(self):
        """Stop the motor."""
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        return "stop"
    
    def run(self):
        """Run the motor in the current direction."""
        if self.direction == 1:
            return self.forward()
        else:
            return self.backward()
    
    def set_speed(self, speed):
        """
        Set the motor speed.
        
        Args:
            speed (str or int): 'l'/'low' or 25, 'm'/'medium' or 50, 'h'/'high' or 75,
                               or any integer from 0-100 for custom duty cycle
        """
        if speed == 'l' or speed == 'low':
            self.pwm.ChangeDutyCycle(25)
            return "low speed"
        elif speed == 'm' or speed == 'medium':
            self.pwm.ChangeDutyCycle(50)
            return "medium speed"
        elif speed == 'h' or speed == 'high':
            self.pwm.ChangeDutyCycle(75)
            return "high speed"
        elif isinstance(speed, int) and 0 <= speed <= 100:
            self.pwm.ChangeDutyCycle(speed)
            return f"custom speed: {speed}%"
        else:
            return "invalid speed setting"
    
    def cleanup(self):
        """Clean up GPIO resources."""
        self.stop()
        self.pwm.stop()
        GPIO.cleanup()
        
    def _encoder_callback(self, channel):
        """
        Callback function for encoder pulse counting.
        Implements quadrature decoding to determine direction and count.
        
        Args:
            channel: The GPIO channel that triggered the callback
        """
        # Read current state of encoder channels
        a = GPIO.input(self.encoder_a)
        b = GPIO.input(self.encoder_b)
        
        # Determine direction based on the sequence of pulses
        if a != self.last_encoder_a:  # State change detected
            self.last_encoder_a = a
            if a == 1:  # Rising edge
                if b == 0:  # Forward direction
                    self.pulse_count += 1
                else:  # Backward direction
                    self.pulse_count -= 1
    
    def reset_encoder(self):
        """Reset the encoder counter to zero."""
        self.pulse_count = 0
    
    def get_position(self):
        """Get the current position in encoder pulses."""
        return self.pulse_count
    
    def move_angle(self, degrees, speed=25, pulses_per_revolution=360):
        """
        Move the motor by precisely the specified angle using encoder feedback.
        
        Args:
            degrees (float): The angle to rotate in degrees (positive for forward, negative for backward)
            speed (int): Speed to use (duty cycle percentage)
            pulses_per_revolution (int): The number of encoder pulses per full revolution
                                        (requires calibration for your specific encoder)
        
        Returns:
            str: Confirmation message
        """
        # Calculate target pulses to move
        pulses_per_degree = pulses_per_revolution / 360.0
        target_pulses = int(abs(degrees) * pulses_per_degree)
        
        # Reset encoder counter
        self.reset_encoder()
        
        # Set direction and speed
        if degrees >= 0:
            self.forward()
        else:
            self.backward()
        self.set_speed(speed)
        
        # Monitor encoder pulses until target is reached
        start_count = self.pulse_count
        
        while abs(self.pulse_count - start_count) < target_pulses:
            sleep(0.01)  # Small delay to prevent CPU hogging
            
        # Stop the motor once the target is reached
        self.stop()
        
        actual_degrees = abs(self.pulse_count - start_count) / pulses_per_degree
        return f"Moved {actual_degrees:.2f} degrees"

# Example of how to use the Motor class
if __name__ == "__main__":
    motor_control()  # Run the original function if this file is executed directly