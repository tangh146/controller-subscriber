import RPi.GPIO as GPIO
import time

class DHT11:
    def __init__(self, pin):
        self.pin = pin
        self.temperature = None
        self.humidity = None
        # Use BCM GPIO references instead of physical pin numbers
        GPIO.setmode(GPIO.BCM)

    def read(self):
        # Send initial signal to DHT11
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.018)  # Hold low for 18ms to trigger DHT11
        GPIO.output(self.pin, GPIO.HIGH)
        
        # Switch to input mode and pull-up resistor
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Wait for sensor to respond
        count = 0
        while GPIO.input(self.pin) == GPIO.HIGH:
            count += 1
            if count > 100:
                return False  # Timeout waiting for response
                
        # Read 40 bits of data (5 bytes)
        data = []
        for i in range(40):
            # Wait for falling edge (start of bit)
            count = 0
            while GPIO.input(self.pin) == GPIO.LOW:
                count += 1
                if count > 100:
                    return False
                    
            # Measure duration of HIGH signal
            count = 0
            start = time.time()
            while GPIO.input(self.pin) == GPIO.HIGH:
                count += 1
                if count > 100:
                    break
            duration = time.time() - start
            
            # Interpret as 0 or 1 (longer HIGH means 1)
            if duration > 0.00004:  # 40 microseconds threshold
                data.append(1)
            else:
                data.append(0)
        
        # Convert bits to bytes
        bytes_data = []
        for i in range(0, 40, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | data[i + j]
            bytes_data.append(byte)
        
        # Validate checksum (bytes_data[4] should equal sum of first 4 bytes)
        if bytes_data[4] == ((bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF):
            self.humidity = bytes_data[0]  # Humidity integral part
            self.temperature = bytes_data[2]  # Temperature integral part
            return True
        else:
            return False  # Checksum failed
        
    def cleanup(self):
        GPIO.cleanup()

# Example usage
if __name__ == "__main__":
    try:
        # DHT11 data pin connected to GPIO4 (Pin 7)
        sensor = DHT11(6)
        
        while True:
            if sensor.read():
                print(f"Temperature: {sensor.temperature}°C, Humidity: {sensor.humidity}%")
            else:
                print("Failed to read from DHT11 sensor")
            time.sleep(2)  # DHT11 sampling rate is 1Hz, wait at least 1 second
            
    except KeyboardInterrupt:
        sensor.cleanup()
        print("Program terminated")