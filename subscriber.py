import json
import paho.mqtt.client as mqtt
from pyee import EventEmitter

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

__all__ = ['ee', 'start_subscriber']