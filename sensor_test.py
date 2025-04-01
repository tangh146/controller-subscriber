import time
import board
import adafruit_dht

# --- Configuration ---
SENSOR_TYPE = adafruit_dht.DHT11
SENSOR_PIN = board.D4
# --- End Configuration ---

try:
    dhtDevice = SENSOR_TYPE(SENSOR_PIN)
    print("DHT11 Sensor Initialized")
except Exception as error:
    print(f"Error initializing sensor: {error.args[0]}")

print("Starting measurements (press CTRL+C to exit)...")

while True:
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        if humidity is not None and temperature_c is not None:
            temperature_f = temperature_c * (9 / 5) + 32
            print(f"Temp: {temperature_c:.1f} C / {temperature_f:.1f} F | Humidity: {humidity:.1f}%")
        else:
            print("Sensor reading failed, trying again...")

    except RuntimeError as error:
        print(f"Runtime Error reading sensor: {error.args[0]}")
        time.sleep(2.0)
        continue

    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)