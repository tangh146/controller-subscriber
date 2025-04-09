import json
import paho.mqtt.client as mqtt
from pyee import EventEmitter

from dotenv import load_dotenv
import os
# from subscriber import ee, start_subscriber
import RPi.GPIO as GPIO          
import time
from worm import Worm
from elevator import run_elevator_with_servo

# Load environment variables
load_dotenv()

# Event emitter used by your motor control logic
ee = EventEmitter()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    # Subscribe to your existing product purchase topic
    client.subscribe("defarm/product/purchased")
    # Additionally subscribe to all remote control topics
    client.subscribe("defarm/remote/#")

def on_message(client, userdata, msg):
    topic = msg.topic
    if topic == "defarm/product/purchased":
        # Original product purchase logic
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            instructions = payload.get("instructions")

            if not isinstance(instructions, list):
                print("Received invalid instruction payload:", payload)
                return

            print("Received instruction sequence:", instructions)

            for instruction in instructions:
                worm.rotate_degrees(instruction)

            # grabber swivel drop
            run_elevator_with_servo()
            # Emit instruction sequence to the motor controller
            ee.emit("purchase", instructions)
        except Exception as e:
            print("Error processing MQTT message:", e)
    elif topic.startswith("defarm/remote/"):
        # New remote control logic: handle any message published under defarm/remote/...
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            print("Received remote control command on {}: {}".format(topic, payload))
            # Emit an event with the topic as key and payload as value
            ee.emit(topic, payload)
        except Exception as e:
            print("Error processing remote MQTT message on topic {}: {}".format(topic, e))
    else:
        print("Received message on unexpected topic {}: {}".format(topic, msg.payload))

def start_subscriber(broker_host, broker_port, username=None, password=None):
    client = mqtt.Client()

    if username and password:
        client.username_pw_set(username, password)

    client.tls_set()  # uses default TLS configuration

    def on_log(client, userdata, level, buf):
        print("LOG:", buf)

    client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT broker at {broker_host}:{broker_port}...")
    try:
        client.connect(broker_host, broker_port, 60)
    except Exception as e:
        print("Connection error:", e)
        return

    client.loop_forever()

if __name__ == "__main__":
	# start all sensors
	
    # start_monitoring()
	
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
    start_subscriber(broker_host, broker_port, username, password)

__all__ = ['ee', 'start_subscriber']