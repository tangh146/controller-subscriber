#!/usr/bin/python3
import smbus
import time

# MPU6050 Register Addresses
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
ACCEL_CONFIG = 0x1C
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47
TEMP_OUT_H   = 0x41

# Initialize the bus
try:
    bus = smbus.SMBus(1)
    print("I2C bus initialized successfully")
except Exception as e:
    print(f"Failed to initialize I2C bus: {e}")
    exit(1)

# MPU6050 device address
device_address = 0x68  # Default MPU6050 address

# Wake up the MPU6050
try:
    bus.write_byte_data(device_address, PWR_MGMT_1, 0)
    print("MPU6050 woken up successfully")
except Exception as e:
    print(f"Failed to wake up MPU6050: {e}")
    print("Check connections and make sure device is correctly wired")
    exit(1)

def read_raw_data(addr):
    try:
        # Read high and low 8-bit values
        high = bus.read_byte_data(device_address, addr)
        low = bus.read_byte_data(device_address, addr+1)
        
        # Concatenate higher and lower value
        value = ((high << 8) | low)
        
        # Get signed value
        if value > 32767:
            value = value - 65536
        return value
    except Exception as e:
        print(f"Error reading data from address {addr}: {e}")
        return 0

# Configure sampling rate and filters
try:
    bus.write_byte_data(device_address, SMPLRT_DIV, 7)
    bus.write_byte_data(device_address, CONFIG, 0)
    bus.write_byte_data(device_address, GYRO_CONFIG, 0)  # 250 deg/s
    bus.write_byte_data(device_address, ACCEL_CONFIG, 0)  # 2g
    print("MPU6050 configuration complete")
    time.sleep(0.1)  # Wait for configuration to settle
except Exception as e:
    print(f"Failed to configure MPU6050: {e}")
    exit(1)

print("\nMPU6050 Test - Press Ctrl+C to stop")
print("------------------------------------")

try:
    while True:
        # Read Accelerometer raw values
        acc_x = read_raw_data(ACCEL_XOUT_H) / 16384.0  # Convert to g
        acc_y = read_raw_data(ACCEL_YOUT_H) / 16384.0
        acc_z = read_raw_data(ACCEL_ZOUT_H) / 16384.0
        
        # Read Gyroscope raw values
        gyro_x = read_raw_data(GYRO_XOUT_H) / 131.0  # Convert to degrees/sec
        gyro_y = read_raw_data(GYRO_YOUT_H) / 131.0
        gyro_z = read_raw_data(GYRO_ZOUT_H) / 131.0
        
        # Read temperature
        temp = read_raw_data(TEMP_OUT_H) / 340.0 + 36.53  # Convert to C
        
        # Print data
        print(f"\rAcc: X={acc_x:.2f}g Y={acc_y:.2f}g Z={acc_z:.2f}g | Gyro: X={gyro_x:.2f}°/s Y={gyro_y:.2f}°/s Z={gyro_z:.2f}°/s | Temp: {temp:.1f}°C", end="")
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nTest stopped by user")
except Exception as e:
    print(f"\nError during testing: {e}")