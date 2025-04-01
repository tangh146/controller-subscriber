import time
import board
import adafruit_dht

# Define two DHT11 sensors on different GPIO pins
# Change the pin numbers (D4 and D17) according to your Raspberry Pi/board connections
sensor1 = adafruit_dht.DHT11(board.D19, use_pulseio=False)
sensor2 = adafruit_dht.DHT11(board.D26, use_pulseio=False)  # Using a different GPIO pin

while True:
    # Create variables to store readings
    temp1_c = None
    temp1_f = None
    humidity1 = None
    
    temp2_c = None
    temp2_f = None
    humidity2 = None
    
    # Read from first sensor
    try:
        temp1_c = sensor1.temperature
        temp1_f = temp1_c * (9 / 5) + 32
        humidity1 = sensor1.humidity
        print("Sensor 1: Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(
            temp1_c, temp1_f, humidity1))
    except RuntimeError as error:
        print("Sensor 1 error:", error.args[0])
    except Exception as error:
        sensor1.exit()
        raise error
    
    # Small delay between sensor readings to avoid potential issues
    time.sleep(0.5)
    
    # Read from second sensor
    try:
        temp2_c = sensor2.temperature
        temp2_f = temp2_c * (9 / 5) + 32
        humidity2 = sensor2.humidity
        print("Sensor 2: Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(
            temp2_c, temp2_f, humidity2))
    except RuntimeError as error:
        print("Sensor 2 error:", error.args[0])
    except Exception as error:
        sensor2.exit()
        raise error
    
    print("-" * 40)  # Print a separator line between reading cycles
    
    # Wait before next reading cycle
    time.sleep(2.5)