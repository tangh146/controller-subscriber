import RPi.GPIO as GPIO
from time import sleep
GPIO.cleanup()

def motor_control(in1=24, in2=23, en=25, encoder_a=17, encoder_b=27, mode='interactive'):
    """
    Control a DC motor with encoder support.
    
    Args:
        in1 (int): GPIO pin for motor input 1
        in2 (int): GPIO pin for motor input 2
        en (int): GPIO pin for motor enable (PWM)
        encoder_a (int): GPIO pin for encoder channel A
        encoder_b (int): GPIO pin for encoder channel B
        mode (str): Control mode - 'interactive' for command-line control or 'angle' for angle movement
    
    Returns:
        None or function depending on mode
    """
    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en, GPIO.OUT)
    
    # Initialize encoder if pins are provided
    pulse_count = 0
    last_encoder_a = 0
    
    def encoder_callback(channel):
        nonlocal pulse_count, last_encoder_a
        a = GPIO.input(encoder_a)
        b = GPIO.input(encoder_b)
        
        if a != last_encoder_a:
            last_encoder_a = a
            if a == 1:
                if b == 0:
                    pulse_count += 1
                else:
                    pulse_count -= 1
    
    # Setup encoder pins if provided
    if encoder_a is not None and encoder_b is not None:
        GPIO.setup(encoder_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(encoder_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(encoder_a, GPIO.BOTH, callback=encoder_callback)
    
    # Set initial motor state
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    
    # Setup PWM
    p = GPIO.PWM(en, 1000)
    p.start(25)  # Start with 25% duty cycle
    
    # Initial direction (1=forward, 0=backward)
    temp1 = 1
    
    # Motor control functions
    def stop():
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
    
    def forward():
        nonlocal temp1
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        temp1 = 1
    
    def backward():
        nonlocal temp1
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        temp1 = 0
    
    def run():
        if temp1 == 1:
            forward()
        else:
            backward()
    
    def set_speed(speed):
        if speed == 'l' or speed == 'low':
            p.ChangeDutyCycle(25)
        elif speed == 'm' or speed == 'medium':
            p.ChangeDutyCycle(50)
        elif speed == 'h' or speed == 'high':
            p.ChangeDutyCycle(75)
        elif isinstance(speed, int) and 0 <= speed <= 100:
            p.ChangeDutyCycle(speed)
    
    def reset_encoder():
        nonlocal pulse_count
        pulse_count = 0
    
    def get_position():
        return pulse_count
    
    def move_angle(degrees, speed=25, pulses_per_revolution=360):
        """
        Move the motor by precisely the specified angle using encoder feedback.
        
        Args:
            degrees (float): The angle to rotate in degrees (positive for forward, negative for backward)
            speed (int): Speed to use (duty cycle percentage)
            pulses_per_revolution (int): The number of encoder pulses per full revolution
        """
        # Calculate target pulses to move
        pulses_per_degree = pulses_per_revolution / 360.0
        target_pulses = int(abs(degrees) * pulses_per_degree)
        
        # Reset encoder counter
        reset_encoder()
        
        # Set direction and speed
        if degrees >= 0:
            forward()
        else:
            backward()
        set_speed(speed)
        
        # Monitor encoder pulses until target is reached
        start_count = get_position()
        
        while abs(get_position() - start_count) < target_pulses:
            sleep(0.01)  # Small delay to prevent CPU hogging
            
        # Stop the motor once the target is reached
        stop()
        
        actual_degrees = abs(get_position() - start_count) / pulses_per_degree
        return f"Moved {actual_degrees:.2f} degrees"
    
    def cleanup():
        stop()
        p.stop()
        GPIO.cleanup()
    
    # Different modes of operation
    if mode == 'angle':
        # Return functions for angle-based control
        return {
            'move_angle': move_angle,
            'forward': forward,
            'backward': backward,
            'stop': stop,
            'set_speed': set_speed,
            'get_position': get_position,
            'reset_encoder': reset_encoder,
            'cleanup': cleanup
        }
    else:
        # Interactive command-line control mode
        print("\n")
        print("The default speed & direction of motor is LOW & Forward.....")
        print("r-run s-stop f-forward b-backward l-low m-medium h-high a-angle e-exit")
        print("\n")
        
        while True:
            try:
                x = input()  # Using input() for Python 3
            except NameError:
                # Fall back to raw_input for Python 2
                x = raw_input()
                
            if x == 'r':
                print("run")
                run()
                
            elif x == 's':
                print("stop")
                stop()
                
            elif x == 'f':
                print("forward")
                forward()
                
            elif x == 'b':
                print("backward")
                backward()
                
            elif x == 'l':
                print("low")
                set_speed('l')
                
            elif x == 'm':
                print("medium")
                set_speed('m')
                
            elif x == 'h':
                print("high")
                set_speed('h')
                
            elif x == 'a':
                # Angle movement mode
                try:
                    angle = float(input("Enter angle in degrees (positive for forward, negative for backward): "))
                    result = move_angle(angle)
                    print(result)
                except ValueError:
                    print("Invalid angle. Please enter a number.")
                
            elif x == 'e':
                print("exit")
                cleanup()
                break
                
            else:
                print("<<< wrong data >>>")
                print("please enter the defined data to continue.....") 