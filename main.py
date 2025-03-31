from dotenv import load_dotenv
import os
from subscriber import ee, start_subscriber
from smotor import TB6600StepperMotor
import RPi.GPIO as GPIO          
from time import sleep

# Load environment variables
load_dotenv()

# Initialize the stepper motor first, before the event handler
smotor = TB6600StepperMotor(pulse_pin=20, dir_pin=21, enable_pin=None, steps_per_rev=4800)

# Also initialize the L298N motor controller through the stepper motor instance
l298n_motor = smotor.initialize_l298n_motor()

# This function will be called when a purchase is made
@ee.on("purchase")
def on_purchase(pots_away):
    print(f"RECEIVED MESSAGE = {pots_away}")
    # This will run the TB6600 stepper motor first, then the L298N motor
    smotor.move(360)

# Set up subscriber
if __name__ == "__main__":
    smotor.move(3200)
    broker_host = os.getenv("MQTT_HOST")
    broker_port = int(os.getenv("MQTT_PORT"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
   
    print("Start MQTT subscriber...")
    start_subscriber(broker_host, broker_port, username, password)
    
