#!/usr/bin/env python3
"""
Raspberry Pi 4B VL53L0X-V2 Distance Sensor Program
This program demonstrates reading distance data from a VL53L0X-V2 sensor using smbus2.
"""

import time
import smbus2
import struct

# VL53L0X I2C address
VL53L0X_ADDR = 0x29

# Register addresses
REG_IDENTIFICATION_MODEL_ID = 0xC0
REG_VHV_CONFIG_PAD_SCL_SDA__EXTSUP_HV = 0x89
REG_MSRC_CONFIG_CONTROL = 0x60
REG_FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT = 0x44
REG_GLOBAL_CONFIG_VCSEL_WIDTH = 0x32
REG_GLOBAL_CONFIG_SPAD_ENABLES_REF_0 = 0xB0
REG_DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD = 0x4E
REG_DYNAMIC_SPAD_REF_EN_START_OFFSET = 0x4F
REG_SYSTEM_SEQUENCE_CONFIG = 0x01
REG_RESULT_RANGE_STATUS = 0x14

# Initialize I2C bus
bus = smbus2.SMBus(1)

def write_byte_data(reg, data):
    """Write a byte to the specified register."""
    bus.write_byte_data(VL53L0X_ADDR, reg, data)

def write_register(reg, data):
    """Write multiple bytes to a register."""
    data = [((reg >> 8) & 0xFF), reg & 0xFF] + data
    bus.write_i2c_block_data(VL53L0X_ADDR, data[0], data[1:])

def read_byte_data(reg):
    """Read a byte from the specified register."""
    return bus.read_byte_data(VL53L0X_ADDR, reg)

def read_block_data(reg, length):
    """Read a block of data from the specified register."""
    return bus.read_i2c_block_data(VL53L0X_ADDR, reg, length)

def initialize_sensor():
    """Initialize the VL53L0X sensor."""
    # Check sensor ID
    val = read_byte_data(REG_IDENTIFICATION_MODEL_ID)
    print(f"Sensor ID: 0x{val:02x}")
    if val != 0xEE:
        raise RuntimeError("Failed to find expected ID register values")
    
    # Set I2C standard mode
    write_byte_data(0x88, 0x00)
    write_byte_data(0x80, 0x01)
    write_byte_data(0xFF, 0x01)
    write_byte_data(0x00, 0x00)
    write_byte_data(0x91, 0x3C)
    write_byte_data(0xFF, 0x00)
    write_byte_data(0x80, 0x00)
    
    # Enable the sensor
    write_byte_data(0x80, 0x01)
    write_byte_data(0xFF, 0x01)
    write_byte_data(0x00, 0x00)
    write_byte_data(0x91, 0x3C)
    write_byte_data(0x00, 0x01)
    write_byte_data(0xFF, 0x00)
    write_byte_data(0x80, 0x00)
    
    print("Sensor initialized")

def get_distance():
    """Perform a single range measurement and return the result in mm."""
    # Start measurement
    write_byte_data(0x80, 0x01)
    write_byte_data(0xFF, 0x01)
    write_byte_data(0x00, 0x00)
    write_byte_data(0x91, 0x3C)
    write_byte_data(0x00, 0x01)
    write_byte_data(0xFF, 0x00)
    write_byte_data(0x80, 0x00)
    
    write_byte_data(0x00, 0x01)
    
    # Wait for measurement to complete
    start = time.time()
    while (read_byte_data(0x00) & 0x01) == 0x01:
        if time.time() - start > 1.0:
            raise RuntimeError("Timeout waiting for measurement")
        time.sleep(0.01)
    
    # Read distance
    data = read_block_data(REG_RESULT_RANGE_STATUS, 12)
    range_mm = (data[10] << 8) | data[11]
    
    return range_mm

# Main program
try:
    print("VL53L0X Distance Sensor Test")
    initialize_sensor()
    print("Press Ctrl+C to exit")
    
    while True:
        try:
            # Get distance reading in millimeters
            distance = get_distance()
            
            # Convert to centimeters for easier reading
            distance_cm = distance / 10.0
            
            print(f"Distance: {distance} mm ({distance_cm:.1f} cm)")
            
            # Adjust the delay according to your needs
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Measurement error: {e}")
            time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nProgram stopped by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Reset the I2C bus
    bus.close()