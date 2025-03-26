import smbus2 as smbus
import time
import math
import json
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import threading

# Flask app setup
app = Flask(__name__, static_folder='static', template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# MPU6050 Register Map
PWR_MGMT_1 = 0x6B
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
ACCEL_CONFIG = 0x1C
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47
TEMP_OUT_H = 0x41

# Initialize the I2C bus
try:
    bus = smbus.SMBus(1)
    print("I2C bus initialized successfully")
except Exception as e:
    print(f"Failed to initialize I2C bus: {e}")
    exit(1)

Device_Address = 0x68  # MPU6050 device address

# MPU6050 initialization
def initialize_MPU():
    try:
        # Wake up the MPU6050
        bus.write_byte_data(Device_Address, PWR_MGMT_1, 0)
        print("MPU6050 woken up successfully")
        
        # Short delay to ensure device is ready
        time.sleep(0.1)
        
        # Configure sampling rate
        bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
        
        # Configure low pass filter
        bus.write_byte_data(Device_Address, CONFIG, 0)
        
        # Configure gyroscope range (±250°/s)
        bus.write_byte_data(Device_Address, GYRO_CONFIG, 0)
        
        # Configure accelerometer range (±2g)
        bus.write_byte_data(Device_Address, ACCEL_CONFIG, 0)
        
        print("MPU6050 initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize MPU6050: {e}")
        print("Check your wiring connections and I2C address")
        return False

# Read raw data from MPU6050
def read_raw_data(addr):
    try:
        # Read high and low 8-bit data
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr+1)
        
        # Concatenate higher and lower values
        value = ((high << 8) | low)
        
        # Get signed value
        if value > 32767:
            value = value - 65536
        return value
    except Exception as e:
        print(f"Error reading data from register {hex(addr)}: {e}")
        return 0  # Return zero on error

# Function to read sensor data and emit via socket
def read_sensor():
    print("Starting sensor data reading thread...")
    if not initialize_MPU():
        print("Failed to initialize MPU6050. Check connections and try again.")
        return
    
    print("Entering sensor reading loop...")
    while True:
        try:
            # Read accelerometer data
            acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0  # Convert to 'g'
            acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
            acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
            
            # Read gyroscope data
            gyro_x = read_raw_data(GYRO_XOUT_H) / 131.0  # Convert to degrees/s
            gyro_y = read_raw_data(GYRO_YOUT_H) / 131.0
            gyro_z = read_raw_data(GYRO_ZOUT_H) / 131.0
            
            # Read temperature data
            temp = read_raw_data(TEMP_OUT_H) / 340.0 + 36.53  # Convert to celsius
            
            # Calculate roll and pitch (in degrees)
            roll = math.atan2(acc_y, acc_z) * 180 / math.pi
            pitch = math.atan2(-acc_x, math.sqrt(acc_y**2 + acc_z**2)) * 180 / math.pi
            
            # Create data dictionary
            data = {
                'timestamp': time.time(),
                'accelerometer': {
                    'x': round(acc_x, 3),
                    'y': round(acc_y, 3),
                    'z': round(acc_z, 3)
                },
                'gyroscope': {
                    'x': round(gyro_x, 3),
                    'y': round(gyro_y, 3),
                    'z': round(gyro_z, 3)
                },
                'orientation': {
                    'roll': round(roll, 2),
                    'pitch': round(pitch, 2)
                },
                'temperature': round(temp, 2)
            }
            
            # Debug print - comment out after testing
            print(f"\rAcc: X={acc_x:.2f}g Y={acc_y:.2f}g Z={acc_z:.2f}g | Gyro: X={gyro_x:.2f}°/s Y={gyro_y:.2f}°/s Z={gyro_z:.2f}°/s", end="")
            
            # Emit data via socket
            socketio.emit('sensor_data', data)
            time.sleep(0.1)  # 10 Hz update rate
            
        except Exception as e:
            print(f"\nError reading sensor data: {e}")
            print("Will retry in 1 second...")
            time.sleep(1)
            # Try to reinitialize the sensor if there was an error
            initialize_MPU()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current')
def current_data():
    # For REST API access
    try:
        acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0
        acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
        acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
        
        gyro_x = read_raw_data(GYRO_XOUT_H) / 131.0
        gyro_y = read_raw_data(GYRO_YOUT_H) / 131.0
        gyro_z = read_raw_data(GYRO_ZOUT_H) / 131.0
        
        temp = read_raw_data(TEMP_OUT_H) / 340.0 + 36.53
        
        roll = math.atan2(acc_y, acc_z) * 180 / math.pi
        pitch = math.atan2(-acc_x, math.sqrt(acc_y**2 + acc_z**2)) * 180 / math.pi
        
        data = {
            'timestamp': time.time(),
            'accelerometer': {
                'x': round(acc_x, 3),
                'y': round(acc_y, 3),
                'z': round(acc_z, 3)
            },
            'gyroscope': {
                'x': round(gyro_x, 3),
                'y': round(gyro_y, 3),
                'z': round(gyro_z, 3)
            },
            'orientation': {
                'roll': round(roll, 2),
                'pitch': round(pitch, 2)
            },
            'temperature': round(temp, 2)
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("MPU6050 Sensor Dashboard - Starting...")
    
    # Check if MPU6050 can be initialized before starting Flask
    try:
        success = initialize_MPU()
        if not success:
            print("Failed to initialize MPU6050. Please check your connections and try again.")
            exit(1)
        
        # Test reading data once
        print("Testing sensor reading...")
        acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0
        acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
        acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
        print(f"Initial accelerometer readings: X={acc_x:.2f}g Y={acc_y:.2f}g Z={acc_z:.2f}g")
        print("Sensor test successful!")
    except Exception as e:
        print(f"Error during initial sensor test: {e}")
        print("Please check your sensor connections and try again.")
        exit(1)
    
    print("Starting Flask server...")
    # Start sensor reading in a separate thread
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.daemon = True
    sensor_thread.start()
    
    # Start the Flask app
    print("Server starting at http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)