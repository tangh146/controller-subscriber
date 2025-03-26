import smbus2 as smbus
import time
import math
import json
import threading
import pymysql
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

# Flask app setup
app = Flask(__name__, static_folder='static', template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'capstonedb.cdgiowwqo0xt.ap-southeast-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'admin',
    'password': 'defarm1234',
    'database': 'sensor_data'  # We'll create this database if it doesn't exist
}

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

# Setup MySQL database and tables
def setup_database():
    try:
        # First connect without specifying a database
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Connect to the database
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # Create accelerometer data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accelerometer_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            acc_x FLOAT,
            acc_y FLOAT,
            acc_z FLOAT
        )
        """)
        
        # Create a table to store the latest readings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_reading (
            id INT PRIMARY KEY DEFAULT 1,
            timestamp DATETIME,
            acc_x FLOAT,
            acc_y FLOAT,
            acc_z FLOAT
        )
        """)
        
        # Insert a default record into latest_reading if it doesn't exist
        cursor.execute("SELECT COUNT(*) FROM latest_reading")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO latest_reading (id, timestamp, acc_x, acc_y, acc_z)
            VALUES (1, NOW(), 0, 0, 0)
            """)
        
        conn.commit()
        print("Database setup complete")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        exit(1)

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

# Save sensor data to MySQL database
def save_to_database(acc_x, acc_y, acc_z):
    try:
        # Connect to database
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # Insert into accelerometer_data table
        cursor.execute("""
        INSERT INTO accelerometer_data (timestamp, acc_x, acc_y, acc_z)
        VALUES (%s, %s, %s, %s)
        """, (datetime.now(), acc_x, acc_y, acc_z))
        
        # Update latest_reading table
        cursor.execute("""
        UPDATE latest_reading
        SET timestamp = %s, acc_x = %s, acc_y = %s, acc_z = %s
        WHERE id = 1
        """, (datetime.now(), acc_x, acc_y, acc_z))
        
        # Limit table to the most recent 20 entries
        cursor.execute("""
        DELETE FROM accelerometer_data 
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT id FROM accelerometer_data 
                ORDER BY timestamp DESC 
                LIMIT 20
            ) AS latest_20
        )
        """)
        
        conn.commit()
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False

# Retrieve latest sensor data from database
def get_latest_data():
    try:
        # Connect to database
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get latest reading
        cursor.execute("SELECT * FROM latest_reading WHERE id = 1")
        result = cursor.fetchone()
        
        # Close connection
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error retrieving latest data: {e}")
        return None

# Retrieve historical sensor data from database
def get_historical_data(limit=20):
    try:
        # Connect to database
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get historical data - limited to most recent 20 entries
        cursor.execute("""
        SELECT * FROM accelerometer_data
        ORDER BY timestamp DESC
        LIMIT %s
        """, (limit,))
        result = cursor.fetchall()
        
        # Close connection
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Error retrieving historical data: {e}")
        return []

# Function to read sensor data and emit via socket
def read_sensor():
    print("Starting sensor data reading thread...")
    if not initialize_MPU():
        print("Failed to initialize MPU6050. Check connections and try again.")
        return
    
    print("Entering sensor reading loop...")
    sample_count = 0
    db_save_interval = 10  # Save to DB every 10 readings
    
    while True:
        try:
            # Read accelerometer data
            acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0  # Convert to 'g'
            acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
            acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
            
            # Create data dictionary
            data = {
                'timestamp': time.time(),
                'accelerometer': {
                    'x': round(acc_x, 3),
                    'y': round(acc_y, 3),
                    'z': round(acc_z, 3)
                }
            }
            
            # Debug print
            print(f"\rAcc: X={acc_x:.2f}g Y={acc_y:.2f}g Z={acc_z:.2f}g", end="")
            
            # Emit data via socket
            socketio.emit('sensor_data', data)
            
            # Increment counter
            sample_count += 1
            
            # Save to database at specified intervals
            if sample_count % db_save_interval == 0:
                save_to_database(acc_x, acc_y, acc_z)
                print("\nSaved to database")
            
            time.sleep(1)  # 1 Hz update rate
            
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
    # Get latest data from database
    data = get_latest_data()
    if data:
        return jsonify({
            'timestamp': data['timestamp'].timestamp(),
            'accelerometer': {
                'x': data['acc_x'],
                'y': data['acc_y'],
                'z': data['acc_z']
            }
        })
    else:
        return jsonify({'error': 'No data available'})

@app.route('/api/history')
def history_data():
    # Get historical data from database
    data = get_historical_data()
    return jsonify(data)

if __name__ == '__main__':
    print("MPU6050 Sensor Dashboard with MySQL - Starting...")
    
    # Setup database
    setup_database()
    
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