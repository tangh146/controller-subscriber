import time
from board import *
import adafruit_dht
import digitalio  # This should now be available

# For DHT22
sensor = adafruit_dht.DHT22(board.D4)
# For DHT11, uncomment the line below and comment out the DHT22 line above
# sensor = adafruit_dht.DHT11(board.D4)

while True:
    try:
        temperature_c = sensor.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = sensor.humidity
        print("Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(temperature_c, temperature_f, humidity))

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        sensor.exit()
        raise error

    time.sleep(3.0)