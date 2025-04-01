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
    """Read temperature and humidity from DHT11 sensor using GPIO"""
    # Initialize data array and result
    data = [0, 0, 0, 0, 0]
    
    # Send start signal
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.02)
    GPIO.output(pin, GPIO.HIGH)
    
    # Switch to input mode
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Wait for response from sensor
    count = 0
    while GPIO.input(pin) == GPIO.HIGH:
        count += 1
        if count > 100:
            return None, None  # Sensor not responding
    
    # Sensor pulls low for 80us to indicate presence
    count = 0
    while GPIO.input(pin) == GPIO.LOW:
        count += 1
        if count > 100:
            return None, None
    
    # Sensor pulls high for 80us before data transmission
    count = 0
    while GPIO.input(pin) == GPIO.HIGH:
        count += 1
        if count > 100:
            return None, None
    
    # Read 40 bits of data (5 bytes)
    j = 0
    for i in range(40):
        # Each bit starts with a 50us low period
        count = 0
        while GPIO.input(pin) == GPIO.LOW:
            count += 1
            if count > 100:
                return None, None
        
        # Duration of high signal determines bit value
        count = 0
        while GPIO.input(pin) == GPIO.HIGH:
            count += 1
            if count > 100:
                break
        
        # If high pulse is longer than 30us, bit is 1
        if count > 15:
            data[j // 8] |= (1 << (7 - (j % 8)))
        j += 1
    
    # Calculate checksum
    checksum = (data[0] + data[1] + data[2] + data[3]) & 0xFF
    if data[4] != checksum:
        return None, None  # Checksum failed
    
    # Calculate temperature and humidity
    humidity = data[0]
    temperature = data[2]
    
    return temperature, humidity

def read_sensor(pin, sensor_number):
    """Read temperature and humidity and return formatted data"""
    # Try a few times as DHT11 readings frequently fail
    for _ in range(5):
        temperature, humidity = read_dht11(pin)
        if temperature is not None and humidity is not None:
            return {
                "sensor": sensor_number,
                "temperature": temperature,
                "humidity": humidity,
                "status": "success"
            }
        time.sleep(0.2)
    
    return {
        "sensor": sensor_number,
        "temperature": None,
        "humidity": None,
        "status": "failed"
    }

def main():
    """Main function to read from both sensors"""
    print("DHT11 Temperature and Humidity Sensors Reader (Direct GPIO)")
    print("----------------------------------------------------------")
    print(f"Sensor 1 connected to GPIO{SENSOR1_PIN} (physical pin 29)")
    print(f"Sensor 2 connected to GPIO{SENSOR2_PIN} (physical pin 31)")
    print("Press CTRL+C to exit")
    print()
    
    try:
        while True:
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Read data from both sensors
            sensor1_data = read_sensor(SENSOR1_PIN, 1)
            sensor2_data = read_sensor(SENSOR2_PIN, 2)
            
            # Display sensor 1 data
            print(f"[{timestamp}] Sensor 1 (GPIO{SENSOR1_PIN}):")
            if sensor1_data["status"] == "success":
                print(f"  Temperature: {sensor1_data['temperature']}°C")
                print(f"  Humidity: {sensor1_data['humidity']}%")
            else:
                print("  Failed to read from sensor 1")
            
            # Display sensor 2 data
            print(f"[{timestamp}] Sensor 2 (GPIO{SENSOR2_PIN}):")
            if sensor2_data["status"] == "success":
                print(f"  Temperature: {sensor2_data['temperature']}°C")
                print(f"  Humidity: {sensor2_data['humidity']}%")
            else:
                print("  Failed to read from sensor 2")
            
            print("-" * 40)
            
            # Wait before next reading
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # Clean up GPIO
        GPIO.cleanup()

if __name__ == "__main__":
    main()