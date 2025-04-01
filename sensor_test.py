import RPi.GPIO as GPIO
import time
from datetime import datetime

# Define GPIO pins
SENSOR1_PIN = 5  # GPIO5 (physical pin 29)
SENSOR2_PIN = 6  # GPIO6 (physical pin 31)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def read_dht11(pin):
    """Simplified DHT11 reading function"""
    # Initialize data array
    data = [0, 0, 0, 0, 0]
    
    # Send start signal
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.018)  # Hold low for 18ms to wake up sensor
    GPIO.output(pin, GPIO.HIGH)
    
    # Switch to input mode
    GPIO.setup(pin, GPIO.IN)
    
    # Wait for sensor response (LOW then HIGH then LOW)
    # Skip first transitions
    for _ in range(40 + 2):  # Skip first 2 transitions
        # Wait for falling edge
        while GPIO.input(pin) == GPIO.HIGH:
            pass
        
        # Wait for rising edge
        while GPIO.input(pin) == GPIO.LOW:
            pass
        
        # Measure high pulse length
        t0 = time.time()
        while GPIO.input(pin) == GPIO.HIGH:
            pass
        t1 = time.time()
        
        # Store bit based on pulse width
        if t1 - t0 > 0.00005:  # 50us threshold
            # 1 bit
            data[0] |= 1
        
        # Shift bits except for last iteration
        if _ < 39 + 2:
            data[0] <<= 1
    
    # Return temperature and humidity
    return data[0] & 0xFF, data[0] >> 8 & 0xFF

def test_single_sensor(pin):
    """Test a single sensor extensively"""
    print(f"Testing sensor on GPIO{pin}...")
    print("Will attempt 5 readings with delays between them.")
    
    for attempt in range(5):
        print(f"  Attempt {attempt + 1}:")
        
        # Reset GPIO state
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)  # Long rest between attempts
        
        try:
            temp, humidity = read_dht11(pin)
            if temp is not None and humidity is not None:
                print(f"    Success! Temperature: {temp}°C, Humidity: {humidity}%")
            else:
                print("    Failed to read sensor data")
        except Exception as e:
            print(f"    Error: {e}")
        
        time.sleep(2)
    
    print(f"Testing of sensor on GPIO{pin} complete.")
    print("-" * 40)

def main():
    """Test each sensor individually"""
    print("DHT11 Sensor Testing Utility")
    print("---------------------------")
    print("This script will test each sensor individually.")
    print("Press CTRL+C at any time to exit.")
    print()
    
    try:
        while True:
            # Test each sensor individually
            test_single_sensor(SENSOR1_PIN)
            test_single_sensor(SENSOR2_PIN)
            
            choice = input("Press Enter to test again or 'q' to quit: ")
            if choice.lower() == 'q':
                break
    
    except KeyboardInterrupt:
        print(