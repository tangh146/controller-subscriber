from dotenv import load_dotenv
import os
from subscriber import ee, start_subscriber
import RPi.GPIO as GPIO          
import time
from worm import Worm
from finding_nemo import run_nema
from dht11 import start_monitoring
import threading


# Load environment variables
load_dotenv()

# This function will be called when a purchase is made
@ee.on("purchase")
def on_purchase(instructions):
    print(f"RECEIVED MESSAGE = {instructions}")
    
    # Optionally read temperature if needed
    # temp = dht_monitor.get_temperature()
    # humid = dht_monitor.get_humidity()

    worm_thread = threading.Thread(target=execute_worm_instructions(instructions))
    nema_ascend_thread = threading.Thread(target=run_nema())

    worm_thread.start()
    nema_ascend_thread.start()

    worm_thread.join()
    nema_ascend_thread.join()

    # grabber swivel drop

def execute_worm_instructions(instructions):
    for instruction in instructions:
        worm.rotate_degrees(instruction)

# This function will be called when a main pump command is received
@ee.on("defarm/remote/main_pump")
def on_main_pump(payload):
    print(f"MAIN PUMP COMMAND RECEIVED: {payload}")

# This function will be called when a drain pump command is received
@ee.on("defarm/remote/drain_pump")
def on_drain_pump(payload):
    print(f"DRAIN PUMP COMMAND RECEIVED: {payload}")

# This function will be called when a peristaltic pump command is received
@ee.on("defarm/remote/peristaltic_pump")
def on_peristaltic_pump(payload):
    print(f"PERISTALTIC PUMP COMMAND RECEIVED: {payload}")

# This function will be called when an LED command is received
@ee.on("defarm/remote/led")
def on_led(payload):
    print(f"LED COMMAND RECEIVED: {payload}")

# This function will be called when a fan command is received
@ee.on("defarm/remote/fan")
def on_fan(payload):
    print(f"FAN COMMAND RECEIVED: {payload}")

# This function will be called when an elevator command is received
@ee.on("defarm/remote/elevator")
def on_elevator(payload):
    print(f"ELEVATOR COMMAND RECEIVED: {payload}")

# This function will be called when a worm command is received
@ee.on("defarm/remote/worm")
def on_worm(payload):
    print(f"WORM COMMAND RECEIVED: {payload}")

# This function will be called when a grabber command is received
@ee.on("defarm/remote/grabber")
def on_grabber(payload):
    print(f"GRABBER COMMAND RECEIVED: {payload}")

# Set up subscriber
if __name__ == "__main__":
	# start all sensors
	
    start_monitoring()
	
    ENABLE_PIN = 22    # PWM pin (BCM numbering)
    IN1_PIN = 23       # Direction pin 1
    IN2_PIN = 24       # Direction pin 2
    ENCODER_A_PIN = 17 # Encoder channel A
    ENCODER_B_PIN = 27
    ROTATION_DEGREES = 2335  # Default rotation angle
    
    worm = Worm(ENABLE_PIN, IN1_PIN, IN2_PIN, ENCODER_A_PIN, ENCODER_B_PIN)

    broker_host = os.getenv("MQTT_HOST")
    broker_port = int(os.getenv("MQTT_PORT"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
   
    # Start DHT monitoring in the background
    #dht_monitor.start_monitoring(interval=3.0, print_values=True)
    
    print("Start MQTT subscriber...")
    try:
        start_subscriber(broker_host, broker_port, username, password)
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        # Clean up resources
        #dht_monitor.cleanup()
        GPIO.cleanup()
        print("Cleanup complete")