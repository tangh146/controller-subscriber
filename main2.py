from dotenv import load_dotenv
import os
from subscriber import ee, start_subscriber
import RPi.GPIO as GPIO          
from time import sleep
import sys

# Import stepper motor and distance sensor modules
from stepper_motor import setup_stepper, dispense_until_distance, cleanup_stepper
from vl53l0x import initialize_sensor, get_distance, cleanup_sensor

# Load environment variables
load_dotenv()

# Target distance to stop at (in centimeters)
TARGET_DISTANCE_CM = 200

# Initialize devices
sensor_initialized = False
stepper_initialized = False

def setup_devices():
    """Initialize both the distance sensor and stepper motor"""
    global sensor_initialized, stepper_initialized
    
    print("Initializing devices...")
    
    # Initialize VL53L0X sensor
    try:
        if initialize_sensor():
            sensor_initialized = True
            print("VL53L0X sensor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize VL53L0X sensor: {e}")
        sensor_initialized = False
    
    # Initialize stepper motor
    try:
        setup_stepper()
        stepper_initialized = True
        print("Stepper motor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize stepper motor: {e}")
        stepper_initialized = False
    
    if not sensor_initialized or not stepper_initialized:
        print("WARNING: Not all devices initialized properly")
    
    return sensor_initialized and stepper_initialized

# This will be called when the program exits
def cleanup():
    """Clean up all devices properly"""
    print("Cleaning up devices...")
    
    if sensor_initialized:
        cleanup_sensor()
    
    if stepper_initialized:
        cleanup_stepper()
    
    GPIO.cleanup()  # Clean up all GPIO

# This function will be called when a purchase is made
@ee.on("purchase")
def on_purchase(pots_away):
    print(f"RECEIVED MESSAGE = {pots_away}")
    
    if not sensor_initialized or not stepper_initialized:
        print("ERROR: Devices not properly initialized, cannot dispense product")
        return
    
    # Dispense product with the stepper motor until target distance is reached
    # You can adjust these parameters based on your needs
    max_steps = 4000     # Maximum steps (prevent endless rotation)
    speed = 15           # RPM
    direction = True     # True for clockwise, False for counterclockwise
    
    result = dispense_until_distance(
        target_distance_cm=TARGET_DISTANCE_CM,
        max_steps=max_steps,
        speed_rpm=speed,
        clockwise=direction,
        get_distance_func=get_distance
    )
    
    if result:
        print(f"Product dispensed successfully (object detected at {TARGET_DISTANCE_CM}cm)")
    else:
        print("Product dispensing may not have completed successfully")

# Set up subscriber
if __name__ == "__main__":
    try:
        # Initialize the hardware
        if not setup_devices():
            print("Failed to initialize all required devices")
            sys.exit(1)
        
        # Test the distance sensor
        current_distance = get_distance()
        if current_distance > 0:
            print(f"Distance sensor test: {current_distance/10.0:.1f}cm")
        else:
            print("WARNING: Distance sensor not working properly")
        
        # Connect to MQTT broker
        broker_host = os.getenv("MQTT_HOST")
        broker_port = int(os.getenv("MQTT_PORT"))
        username = os.getenv("MQTT_USERNAME")
        password = os.getenv("MQTT_PASSWORD")
       
        print("Starting MQTT subscriber...")
        start_subscriber(broker_host, broker_port, username, password)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup()