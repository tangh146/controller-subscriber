import Adafruit_DHT
import time
from datetime import datetime

# Define sensor type
SENSOR_TYPE = Adafruit_DHT.DHT11

# Define GPIO pins connected to the sensors
SENSOR1_PIN = 5  # GPIO5 (physical pin 29)
SENSOR2_PIN = 6  # GPIO6 (physical pin 31)

def read_sensor(sensor_pin, sensor_number):
    """Read temperature and humidity from a DHT11 sensor"""
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR_TYPE, sensor_pin)
    
    if humidity is not None and temperature is not None:
        return {
            "sensor": sensor_number,
            "temperature": temperature,
            "humidity": humidity,
            "status": "success"
        }
    else:
        return {
            "sensor": sensor_number,
            "temperature": None,
            "humidity": None,
            "status": "failed"
        }

def main():
    """Main function to read from both sensors"""
    print("DHT11 Temperature and Humidity Sensors Reader")
    print("--------------------------------------------")
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
            
            # Wait before next reading (DHT11 can only be read once every 1-2 seconds)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")

if __name__ == "__main__":
    main()