import json
import paho.mqtt.client as mqtt
from pyee import EventEmitter

# Global constants and state
TOTAL_POT_COUNT = 25      # Total number of pots; constant
CURRENT_STATE = 1         # Current pot id at the collection point (initialized to 1)

# Create an event emitter instance
ee = EventEmitter()

def compute_pots_away(received_product_id):
    """
    Compute pots_away based on the current state and received product id.
    If CURRENT_STATE > received_product_id:
       pots_away = TOTAL_POT_COUNT - CURRENT_STATE + received_product_id
    Otherwise:
       pots_away = received_product_id - CURRENT_STATE
    """
    try:
        prod_id = int(received_product_id)
    except Exception as e:
        print("Error converting received product id to int:", e)
        return None

    if CURRENT_STATE > prod_id:
        return TOTAL_POT_COUNT - CURRENT_STATE + prod_id
    else:
        return prod_id - CURRENT_STATE

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    # Subscribe to the topic for purchase notifications
    client.subscribe("defarm/product/purchased")

def on_message(client, userdata, msg):
    global CURRENT_STATE  # Declare global so we can update it
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        product_id = payload.get("productId")
        if product_id is None:
            print("Received message without productId")
            return
        pots_away = compute_pots_away(product_id)
        if pots_away is None:
            print("Could not compute pots_away for productId:", product_id)
            return
        # Update CURRENT_STATE to the received product id
        CURRENT_STATE = int(product_id)
        # Emit the "purchase" event with the computed pots_away
        ee.emit("purchase", pots_away)
    except Exception as e:
        print("Error processing message:", e)

def start_subscriber(broker_host, broker_port, username=None, password=None):
    client = mqtt.Client()
    
    # If credentials are provided, set them
    if username and password:
        client.username_pw_set(username, password)
    
    # Enable TLS (assuming your broker uses TLS)
    client.tls_set()  # This sets up TLS with default parameters
    # Optionally, during development, you can disable certificate verification (not recommended for production):
    # client.tls_insecure_set(True)
    
    # Set up debug logging to help diagnose connection issues
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

# Expose the event emitter and the start_subscriber function so that they can be used in main.py.
__all__ = ['ee', 'start_subscriber']