import smbus
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
bus = smbus.SMBus(1)
Device_Address = 0x68  # MPU6050 device address

# MPU6050 initialization
def initialize_MPU():
    # Wake up the MPU6050
    bus.write_byte_data(Device_Address, PWR_MGMT_1, 0)
    
    # Configure sampling rate
    bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
    
    # Configure low pass filter
    bus.write_byte_data(Device_Address, CONFIG, 0)
    
    # Configure gyroscope range (±250°/s)
    bus.write_byte_data(Device_Address, GYRO_CONFIG, 0)
    
    # Configure accelerometer range (±2g)
    bus.write_byte_data(Device_Address, ACCEL_CONFIG, 0)

# Read raw data from MPU6050
def read_raw_data(addr):
    # Read high and low 8-bit data
    high = bus.read_byte_data(Device_Address, addr)
    low = bus.read_byte_data(Device_Address, addr+1)
    
    # Concatenate higher and lower values
    value = ((high << 8) | low)
    
    # Get signed value
    if value > 32767:
        value = value - 65536
    return value

# Function to read sensor data and emit via socket
def read_sensor():
    initialize_MPU()
    
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
            
            # Emit data via socket
            socketio.emit('sensor_data', data)
            time.sleep(0.1)  # 10 Hz update rate
            
        except Exception as e:
            print(f"Error reading sensor data: {e}")
            time.sleep(1)

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
    # Start sensor reading in a separate thread
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.daemon = True
    sensor_thread.start()
    
    # Start the Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)