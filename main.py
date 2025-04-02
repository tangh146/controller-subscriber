from dotenv import load_dotenv
import os
from subscriber import ee, start_subscriber
import RPi.GPIO as GPIO          
import time
from worm import Worm
from nema import run_nema


# Load environment variables
load_dotenv()

# This function will be called when a purchase is made
@ee.on("purchase")
def on_purchase(pots_away):
    print(f"RECEIVED MESSAGE = {pots_away}")
    
    run_nema()
    #time.sleep(0.1)
    for i in range(pots_away):
        worm.rotate_degrees(2335)
    #grabber code here
    
    # run nema reverse
    
    # grabber swivel drop


# Set up subscriber
if __name__ == "__main__":
	# start all sensors
	
	
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
   
    print("Start MQTT subscriber...")
    start_subscriber(broker_host, broker_port, username, password)
    
