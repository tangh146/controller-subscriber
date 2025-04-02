import time
import board
import adafruit_dht
import threading
import requests  # Import requests to perform HTTP POST

class DHT11Monitor:
    """
    A class to continuously monitor DHT11 sensors in the background.
    """
    
    def __init__(self, pin_list=None):
        """
        Initialize DHT11 sensors on specified pins.
        
        Args:
            pin_list (list): List of board pins to connect to DHT11 sensors.
                             Default is [board.D19, board.D26] if None is provided.
        """
        if pin_list is None:
            pin_list = [board.D19, board.D26]
        
        self.sensors = []
        for pin in pin_list:
            self.sensors.append(adafruit_dht.DHT11(pin, use_pulseio=False))
        
        self.num_sensors = len(self.sensors)
        self.latest_readings = [None] * self.num_sensors
        self.running = False
        self.monitor_thread = None
    
    def _read_sensors(self):
        """Read all sensors and return their data."""
        results = []
        
        for i, sensor in enumerate(self.sensors):
            data = {
                'sensor_id': i + 1,
                'temperature_c': None,
                'temperature_f': None,
                'humidity': None,
                'error': None
            }
            
            try:
                data['temperature_c'] = sensor.temperature
                data['temperature_f'] = data['temperature_c'] * (9 / 5) + 32
                data['humidity'] = sensor.humidity
            except RuntimeError as error:
                data['error'] = error.args[0]
            except Exception as error:
                data['error'] = str(error)
            
            results.append(data)
            
            # Small delay between reading sensors
            if i < len(self.sensors) - 1:
                time.sleep(0.5)
        
        return results
    
    def _post_data(self, temperature, humidity):
        """
        Post the sensor readings to the endpoint.
        
        Args:
            temperature (float): Temperature reading from sensor 1.
            humidity (float): Humidity reading from sensor 1.
        """
        # Use the actual sensor values if available; otherwise, use sentinel value -1
        payload = {
            "temperature1": temperature if temperature is not None else -1,
            "temperature2": -1,
            "temperature3": -1,
            "humidity1": humidity if humidity is not None else -1,
            "humidity2": -1,
            "tankWaterLevel": -1,
            "tds": -1,
            "L1WaterLevel": -1,
            "L2WaterLevel": -1
        }
        
        try:
            response = requests.post("http://18.142.255.27:82/data", json=payload, timeout=5)
            # Optionally, you can print the status or response text for debugging:
            print("HTTP POST Response:", response.status_code, response.text)
        except Exception as e:
            print("Failed to POST data:", e)
    
    def _monitor_loop(self, interval=3.0, print_values=False):
        """Background monitoring loop, updates readings continuously."""
        self.running = True
        
        while self.running:
            try:
                readings = self._read_sensors()
                self.latest_readings = readings
                
                # Use sensor 1 values for POST (assuming sensor 1 is the first sensor)
                sensor1 = readings[0] if readings else None
                temperature1 = sensor1.get('temperature_c') if sensor1 and sensor1['error'] is None else None
                humidity1 = sensor1.get('humidity') if sensor1 and sensor1['error'] is None else None

                # Post the data
                self._post_data(temperature1, humidity1)
                
                if print_values:
                    for reading in readings:
                        if reading['error'] is None:
                            print(f"DHT11 Sensor {reading['sensor_id']}: "
                                  f"{reading['temperature_c']}°C, "
                                  f"{reading['humidity']}%")
                        else:
                            print(f"DHT11 Sensor {reading['sensor_id']} error: {reading['error']}")
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in monitoring thread: {str(e)}")
                time.sleep(interval)  # Sleep on error to avoid tight loop
    
    def start(self, interval=3.0, print_values=False):
        """
        Start monitoring sensors in a background thread.
        
        Args:
            interval (float): Time in seconds between readings.
            print_values (bool): Whether to print readings to console.
            
        Returns:
            bool: True if monitoring was started, False if already running.
        """
        if self.running:
            return False
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval, print_values),
            daemon=True  # Thread will exit when main program exits
        )
        self.monitor_thread.start()
        return True
    
    def stop(self):
        """Stop the background monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def get_temperature(self, sensor_id=1):
        """
        Get the latest temperature reading from a specific sensor.
        
        Args:
            sensor_id (int): 1-based index of the sensor to query.
            
        Returns:
            float or None: Temperature in Celsius or None if not available.
        """
        if 1 <= sensor_id <= self.num_sensors:
            reading = self.latest_readings[sensor_id - 1]
            if reading and reading['error'] is None:
                return reading['temperature_c']
        return None
    
    def get_humidity(self, sensor_id=1):
        """
        Get the latest humidity reading from a specific sensor.
        
        Args:
            sensor_id (int): 1-based index of the sensor to query.
            
        Returns:
            float or None: Humidity percentage or None if not available.
        """
        if 1 <= sensor_id <= self.num_sensors:
            reading = self.latest_readings[sensor_id - 1]
            if reading and reading['error'] is None:
                return reading['humidity']
        return None
    
    def get_all_readings(self):
        """
        Get all current sensor readings.
        
        Returns:
            list: List of all current sensor readings.
        """
        return self.latest_readings
    
    def cleanup(self):
        """Properly clean up all sensors."""
        self.stop()
        for sensor in self.sensors:
            try:
                sensor.exit()
            except:
                pass

# Create a global instance for easy importing
monitor = DHT11Monitor()

# Helper functions for simple usage
def start_monitoring(interval=3.0, print_values=False):
    """Start DHT monitoring with the global instance."""
    return monitor.start(interval, print_values)

def get_temperature(sensor_id=1):
    """Get temperature from the global monitor instance."""
    return monitor.get_temperature(sensor_id)

def get_humidity(sensor_id=1):
    """Get humidity from the global monitor instance."""
    return monitor.get_humidity(sensor_id)

def cleanup():
    """Clean up the global monitor instance."""
    monitor.cleanup()

# Example direct usage
if __name__ == "__main__":
    # Start the monitoring
    start_monitoring(print_values=True)
    
    try:
        # Just keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        cleanup()
