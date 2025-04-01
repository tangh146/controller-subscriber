import RPi.GPIO as GPIO
import time
import csv
import os
from datetime import datetime

# Define GPIO pins
SENSOR1_PIN = 5  # GPIO5 (physical pin 29)
SENSOR2_PIN = 6  # GPIO6 (physical pin 31)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define log file
LOG_FILE = "dht11_sensor_data.csv"

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

def log_data(sensor1_data, sensor2_data, log_file):
    """Log sensor data to a CSV file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(log_file)
    
    with open(log_file, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'sensor1_temp', 'sensor1_humidity', 
                     'sensor2_temp', 'sensor2_humidity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'timestamp': timestamp,
            'sensor1_temp': sensor1_data['temperature'] if sensor1_data['status'] == 'success' else 'N/A',
            'sensor1_humidity': sensor1_data['humidity'] if sensor1_data['status'] == 'success' else 'N/A',
            'sensor2_temp': sensor2_data['temperature'] if sensor2_data['status'] == 'success' else 'N/A',
            'sensor2_humidity': sensor2_data['humidity'] if sensor2_data['status'] == 'success' else 'N/A'
        })
    
    return timestamp

def main():
    """Main function to read from both sensors and log data"""
    print("DHT11 Temperature and Humidity Sensors Logger (Direct GPIO)")
    print("----------------------------------------------------------")
    print(f"Sensor 1 connected to GPIO{SENSOR1_PIN} (physical pin 29)")
    print(f"Sensor 2 connected to GPIO{SENSOR2_PIN} (physical pin 31)")
    print(f"Logging data to: {LOG_FILE}")
    print("Press CTRL+C to exit")
    print()
    
    try:
        while True:
            # Read data from both sensors
            sensor1_data = read_sensor(SENSOR1_PIN, 1)
            sensor2_data = read_sensor(SENSOR2_PIN, 2)
            
            # Log data to CSV file
            timestamp = log_data(sensor1_data, sensor2_data, LOG_FILE)
            
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
        print(f"Data has been logged to {LOG_FILE}")
    finally:
        # Clean up GPIO
        GPIO.cleanup()

if __name__ == "__main__":
    main()