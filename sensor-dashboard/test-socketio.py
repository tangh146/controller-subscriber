import time
import threading
import random  # For generating test data if needed
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

# Flask app setup
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global flag to check if we should generate fake data (use if sensor unavailable)
USE_FAKE_DATA = False  # Set to True if you want to test without a real sensor

# Try to import sensor libraries
try:
    import smbus2 as smbus
    
    # MPU6050 Register Map
    PWR_MGMT_1 = 0x6B
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    ACCEL_XOUT_H = 0x3B
    ACCEL_YOUT_H = 0x3D
    ACCEL_ZOUT_H = 0x3F
    
    # Initialize the I2C bus
    try:
        bus = smbus.SMBus(1)
        Device_Address = 0x68  # MPU6050 device address
        print("I2C bus initialized successfully")
    except Exception as e:
        print(f"Failed to initialize I2C bus: {e}")
        print("Switching to fake data mode")
        USE_FAKE_DATA = True
    
except ImportError:
    print("smbus2 library not available, switching to fake data mode")
    USE_FAKE_DATA = True

# MPU6050 initialization
def initialize_MPU():
    global USE_FAKE_DATA
    
    if USE_FAKE_DATA:
        print("Using fake data mode - no sensor initialization needed")
        return True
    
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
        print("Switching to fake data mode")
        USE_FAKE_DATA = True
        return False

# Read raw data from MPU6050
def read_raw_data(addr):
    if USE_FAKE_DATA:
        return 0
    
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

# Function to read sensor data (or generate fake data) and emit via socket
def read_sensor():
    global USE_FAKE_DATA
    
    print("Starting sensor data reading thread...")
    if not USE_FAKE_DATA:
        if not initialize_MPU():
            print("Failed to initialize MPU6050. Switching to fake data.")
            USE_FAKE_DATA = True
    
    print("Entering sensor reading loop...")
    while True:
        try:
            if USE_FAKE_DATA:
                # Generate fake accelerometer data
                acc_x = random.uniform(-1.0, 1.0)
                acc_y = random.uniform(-1.0, 1.0)
                acc_z = random.uniform(-1.0, 1.0)
                print(f"Generated fake data: X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
            else:
                # Read accelerometer data
                acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0  # Convert to 'g'
                acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
                acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
                print(f"Read sensor data: X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
            
            # Create data dictionary
            data = {
                'timestamp': time.time(),
                'accelerometer': {
                    'x': round(acc_x, 3),
                    'y': round(acc_y, 3),
                    'z': round(acc_z, 3)
                }
            }
            
            # Emit data via socket
            print("Emitting sensor_data event...")
            socketio.emit('sensor_data', data, broadcast=True)
            print("Event emitted")
            
            time.sleep(1)  # 1 Hz update rate
            
        except Exception as e:
            print(f"Error in sensor reading: {e}")
            time.sleep(1)

# Routes
@app.route('/')
def index():
    return render_template('test-socketio.html')

@app.route('/api/current')
def current_data():
    global USE_FAKE_DATA
    
    # Get current data - either read from sensor or generate fake data
    if USE_FAKE_DATA:
        acc_x = random.uniform(-1.0, 1.0)
        acc_y = random.uniform(-1.0, 1.0)
        acc_z = random.uniform(-1.0, 1.0)
    else:
        acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0
        acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
        acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
    
    return jsonify({
        'timestamp': time.time(),
        'accelerometer': {
            'x': round(acc_x, 3),
            'y': round(acc_y, 3),
            'z': round(acc_z, 3)
        },
        'using_fake_data': USE_FAKE_DATA
    })

@app.route('/api/status')
def status():
    global USE_FAKE_DATA
    
    return jsonify({
        'status': 'running',
        'using_fake_data': USE_FAKE_DATA,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    print("SocketIO Test Server - Starting...")
    
    # Start sensor reading in a separate thread
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.daemon = True
    sensor_thread.start()
    
    # Start the Flask app
    print("Server starting at http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)