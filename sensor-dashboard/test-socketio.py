import time
import threading
import math
import json
import pymysql
from datetime import datetime
from flask import Flask, jsonify, render_template

# Flask app setup
app = Flask(__name__, static_folder='static', template_folder='templates')

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'capstonedb.cdgiowwqo0xt.ap-southeast-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'admin',
    'password': 'defarm1234',
    'database': 'sensor_data'
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

# Initialize the I2C bus
try:
    import smbus2 as smbus
    bus = smbus.SMBus(1)
    Device_Address = 0x68  # MPU6050 device address
    print("I2C bus initialized successfully")
    USE_FAKE_DATA = False
except Exception as e:
    print(f"Failed to initialize I2C bus: {e}")
    print("Using fake data mode")
    USE_FAKE_DATA = True

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
        
        # Create a table to store the latest reading
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

# MPU6050 initialization
def initialize_MPU():
    if USE_FAKE_DATA:
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
        global USE_FAKE_DATA
        USE_FAKE_DATA = True
        return False

# Read raw data from MPU6050
def read_raw_data(addr):
    if USE_FAKE_DATA:
        import random
        return random.randint(-16384, 16384)
        
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
        
        print(f"Saved to database: X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False

# Get latest sensor data (either from sensor or database)
def get_latest_data(use_sensor=True):
    if use_sensor:
        # Read directly from sensor
        try:
            if initialize_MPU():
                acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0  # Convert to 'g'
                acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
                acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
                
                # Save to database
                save_to_database(acc_x, acc_y, acc_z)
                
                return {
                    'timestamp': datetime.now().timestamp(),
                    'accelerometer': {
                        'x': round(acc_x, 3),
                        'y': round(acc_y, 3),
                        'z': round(acc_z, 3)
                    }
                }
        except Exception as e:
            print(f"Error reading from sensor: {e}")
    
    # Fallback to database if sensor read fails or not requested
    try:
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
        data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if data:
            return {
                'timestamp': data['timestamp'].timestamp() if data['timestamp'] else time.time(),
                'accelerometer': {
                    'x': round(data['acc_x'], 3) if data['acc_x'] is not None else 0,
                    'y': round(data['acc_y'], 3) if data['acc_y'] is not None else 0,
                    'z': round(data['acc_z'], 3) if data['acc_z'] is not None else 0
                }
            }
    except Exception as e:
        print(f"Error getting latest data from database: {e}")
    
    # Default fallback if everything fails
    return {
        'timestamp': time.time(),
        'accelerometer': {
            'x': 0,
            'y': 0,
            'z': 0
        },
        'error': 'Failed to get data from both sensor and database'
    }

# Get historical data from database
def get_historical_data(limit=20):
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get historical data
        cursor.execute("""
        SELECT * FROM accelerometer_data
        ORDER BY timestamp DESC
        LIMIT %s
        """, (limit,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to timestamps for JSON serialization
        data = []
        for row in results:
            data.append({
                'id': row['id'],
                'timestamp': row['timestamp'].timestamp() if row['timestamp'] else None,
                'accelerometer': {
                    'x': round(row['acc_x'], 3) if row['acc_x'] is not None else 0,
                    'y': round(row['acc_y'], 3) if row['acc_y'] is not None else 0,
                    'z': round(row['acc_z'], 3) if row['acc_z'] is not None else 0
                }
            })
        
        return data
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return []

# Background thread to periodically read sensor and save to database
def sensor_reading_thread():
    print("Starting sensor reading thread")
    
    while True:
        try:
            if initialize_MPU():
                # Read accelerometer data
                acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0
                acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
                acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
                
                print(f"Read sensor data: X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
                
                # Save to database
                save_to_database(acc_x, acc_y, acc_z)
            
            # Sleep for a second before next reading
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in sensor reading thread: {e}")
            time.sleep(1)

# Flask routes
@app.route('/')
def index():
    return render_template('http-polling.html')

@app.route('/api/current')
def current_data():
    return jsonify(get_latest_data())

@app.route('/api/history')
def history_data():
    return jsonify(get_historical_data())

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'using_fake_data': USE_FAKE_DATA,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    print("MPU6050 HTTP Polling Dashboard - Starting...")
    
    # Setup database
    setup_database()
    
    # Initialize sensor
    initialize_MPU()
    
    # Start sensor reading in a separate thread
    sensor_thread = threading.Thread(target=sensor_reading_thread)
    sensor_thread.daemon = True
    sensor_thread.start()
    
    # Start the Flask app
    print("Server starting at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)