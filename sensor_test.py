import os
import glob
import time

# Initialize the 1-Wire interface
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Define the base directory for 1-Wire devices
base_dir = '/sys/bus/w1/devices/'
# Find the device folder that starts with 28-
device_folder = glob.glob(base_dir + '28*')[0]
# Define the file path for the device data
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    """Read the raw temperature data from the sensor file"""
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def read_temp():
    """Process the temperature data and return the temperature in Celsius and Fahrenheit"""
    lines = read_temp_raw()
    # Wait until the reading is valid (contains "YES")
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    
    # Find the temperature value in the second line
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        # Extract the temperature value (it's in 1/1000 degrees Celsius)
        temp_string = lines[1][equals_pos+2:]
        # Convert to float and divide by 1000 to get degrees Celsius
        temp_c = float(temp_string) / 1000.0
        # Convert to Fahrenheit
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
    
    return None, None

# Main loop to continuously read temperature
try:
    while True:
        temp_c, temp_f = read_temp()
        print(f'Temperature: {temp_c:.2f}°C / {temp_f:.2f}°F')
        time.sleep(1)  # Wait 1 second between readings

except KeyboardInterrupt:
    print('Temperature monitoring stopped.')