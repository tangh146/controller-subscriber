import RPi.GPIO as GPIO
import time

class ServoController:
    def __init__(self, servo_pins=None):
        """
        Initialize the servo controller with specified GPIO pins.
        
        Args:
            servo_pins (list): List of GPIO pins for servos [servo1_pin, servo2_pin, servo3_pin]
                              Defaults to [17, 18, 27] if not specified
        """
        # Default pin configuration if none provided
        self.servo_pins = servo_pins if servo_pins else [6, 13, 19]
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Set up servo pins as outputs
        for pin in self.servo_pins:
            GPIO.setup(pin, GPIO.OUT)
        
        # Create PWM instances for each servo (50Hz frequency)
        self.servos = []
        for pin in self.servo_pins:
            servo = GPIO.PWM(pin, 50)
            servo.start(0)
            self.servos.append(servo)
    
    def set_angle(self, servo_index, angle):
        """
        Set a servo to a specific angle.
        
        Args:
            servo_index (int): Index of the servo (0, 1, or 2)
            angle (float): Angle to set (0-180 degrees)
        """
        if 0 <= servo_index < len(self.servos):
            duty_cycle = 2.5 + (angle / 18.0)
            self.servos[servo_index].ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)  # Allow time for the servo to reach position
        else:
            print(f"Error: Invalid servo index {servo_index}")
    
    def run_sequence(self, verbose=True):
        """
        Run the predefined sequence of servo movements.
        
        Args:
            verbose (bool): Whether to print status messages
        """
        steps = [
            (1, "Setting initial positions (Servo 1: 0°, Servo 2: 45°, Servo 3: 165°)", 
             [(0, 0), (1, 45), (2, 100)]),
            (2, "Moving Servo 1 to 90°", [(0, 90)]),
            (3, "Moving Servo 1 to 180°", [(0, 180)]),
            (4, "Moving Servo 2 to 130°", [(1, 130)]),
            (5, "Moving Servo 3 to 180°", [(2, 130)]),
            (6, "Moving Servo 2 to 45°", [(1, 45)]),
            (7, "Moving Servo 1 to 90°", [(0, 90)]),
            (8, "Moving Servo 1 to 0°", [(0, 0)]),
            (9, "Moving Servo 3 to 165°", [(2, 100)])
        ]
        
        try:
            for step_num, description, movements in steps:
                if verbose:
                    print(f"Step {step_num}: {description}")
                
                for servo_idx, angle in movements:
                    self.set_angle(servo_idx, angle)
                
                time.sleep(1)  # Wait between steps
            
            if verbose:
                print("Sequence completed!")
                
        except Exception as e:
            print(f"An error occurred: {e}")
    

# Add this main function and if __name__ block
def main():
    controller = ServoController()
    controller.run_sequence()


if __name__ == "__main__":
    main()