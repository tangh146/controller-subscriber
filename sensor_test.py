import pigpio
import time

class DHT11:
    def __init__(self, pi, gpio):
        """
        Initialize the DHT11 sensor.
        
        pi: pigpio pi connection
        gpio: GPIO pin (BCM numbering)
        """
        self.pi = pi
        self.gpio = gpio
        self.temperature = None
        self.humidity = None
        self.data = []
        
        # Set up the callback
        self.cb = None
        self.edge_count = 0
        self.bits = 0
        self.code = 0
        
    def _callback(self, gpio, level, tick):
        """Callback function for the pigpio edge detection"""
        edge = level
        
        if edge == 0: # Falling edge
            if self.edge_count == 0:
                self.bits = 0
                self.code = 0
            elif self.edge_count == 1:
                self.d_high = tick
            else:
                # Calculate the pulse width
                pulse_width = pigpio.tickDiff(self.d_high, tick)
                
                # Interpret as 1 or 0 based on pulse width
                if pulse_width > 100: # Long pulse = 1, short pulse = 0
                    self.bits = (self.bits << 1) | 1
                else:
                    self.bits = self.bits << 1
                    
                # Every 8 bits, store a byte
                if (self.edge_count-1) % 16 == 0:
                    self.code = 0
                if (self.edge_count-1) % 8 == 0:
                    self.data.append(self.bits)
                    self.bits = 0
            
            self.d_high = tick
        self.edge_count += 1
        
    def read(self):
        """Read data from the DHT11 sensor"""
        self.data = []
        self.edge_count = 0
        
        # Set up the callback for edge detection
        self.cb = self.pi.callback(self.gpio, pigpio.EITHER_EDGE, self._callback)
        
        # Send the start signal
        self.pi.set_mode(self.gpio, pigpio.OUTPUT)
        self.pi.write(self.gpio, 0)  # LOW
        time.sleep(0.02)  # 20ms LOW signal to start
        self.pi.write(self.gpio, 1)  # HIGH
        
        # Release the GPIO for the sensor to respond
        self.pi.set_mode(self.gpio, pigpio.INPUT)
        time.sleep(0.2)  # Wait for readings
        
        # Cancel the callback
        if self.cb:
            self.cb.cancel()
            self.cb = None
            
        # Process the data
        if len(self.data) >= 5:
            # Convert bit sequences to bytes
            humidity = self.data[0]
            temperature = self.data[2]
            
            # Validate checksum (byte 4 should equal sum of first 4 bytes)
            checksum = self.data[4]
            if checksum == ((humidity + temperature) & 0xFF):
                self.humidity = humidity
                self.temperature = temperature
                return True
                
        return False
        
    def cleanup(self):
        """Clean up resources"""
        if self.cb:
            self.cb.cancel()

# Example usage
if __name__ == "__main__":
    try:
        # Initialize pigpio
        pi = pigpio.pi()
        if not pi.connected:
            print("Failed to connect to pigpio daemon!")
            exit(1)
        
        # DHT11 connected to GPIO 4 (BCM numbering)
        GPIO_PIN = 4
        
        print("DHT11 Sensor Test - PIGPIO Implementation")
        print(f"Using GPIO PIN: {GPIO_PIN}")
        print("Press CTRL+C to exit")
        
        # Initialize sensor
        sensor = DHT11(pi, GPIO_PIN)
        
        # Try to read the sensor
        max_retries = 15
        retry_count = 0
        
        while retry_count < max_retries:
            print(f"\nAttempt {retry_count + 1}/{max_retries}")
            
            if sensor.read():
                print(f"SUCCESS! Temperature: {sensor.temperature}°C, Humidity: {sensor.humidity}%")
                retry_count = 0  # Reset counter on success
            else:
                print("Failed to read from DHT11 sensor")
                retry_count += 1
                
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # Clean up
        if 'sensor' in locals():
            sensor.cleanup()
        if 'pi' in locals() and pi.connected:
            pi.stop()