from dotenv import load_dotenv
import os
from subscriber import ee, start_subscriber     


# Load environment variables
load_dotenv()

# This function will be called when a purchase is made
@ee.on("purchase")
def on_purchase(instructions):
    print(f"RECEIVED MESSAGE = {instructions}")


# Set up subscriber
if __name__ == "__main__":
    broker_host = os.getenv("MQTT_HOST")
    broker_port = int(os.getenv("MQTT_PORT"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
    
    print("Start MQTT subscriber...")
    start_subscriber(broker_host, broker_port, username, password)