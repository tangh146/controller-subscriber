#!/usr/bin/env python3
"""
VL53L0X Distance Sensor Module
This module provides functions to interact with a VL53L0X time-of-flight distance sensor.
"""

import time
import smbus2

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
bus = None

def initialize_sensor():
    """Initialize the VL53L0X sensor."""
    global bus
    
    # Initialize I2C bus if not already done
    if bus is None:
        bus = smbus2.SMBus(1)
    
    # Check sensor ID
    val = read_byte_data(REG_IDENTIFICATION_MODEL_ID)
    print(f"VL53L0X Sensor ID: 0x{val:02x}")
    if val != 0xEE:
        raise RuntimeError("Failed to find expected VL53L0X ID register value")
    
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
    
    print("VL53L0X Sensor initialized")
    return True

def write_byte_data(reg, data):
    """Write a byte to the specified register."""
    global bus
    if bus is None:
        bus = smbus2.SMBus(1)
    bus.write_byte_data(VL53L0X_ADDR, reg, data)

def write_register(reg, data):
    """Write multiple bytes to a register."""
    global bus
    if bus is None:
        bus = smbus2.SMBus(1)
    data = [((reg >> 8) & 0xFF), reg & 0xFF] + data
    bus.write_i2c_block_data(VL53L0X_ADDR, data[0], data[1:])

def read_byte_data(reg):
    """Read a byte from the specified register."""
    global bus
    if bus is None:
        bus = smbus2.SMBus(1)
    return bus.read_byte_data(VL53L0X_ADDR, reg)

def read_block_data(reg, length):
    """Read a block of data from the specified register."""
    global bus
    if bus is None:
        bus = smbus2.SMBus(1)
    return bus.read_i2c_block_data(VL53L0X_ADDR, reg, length)

def get_distance():
    """
    Perform a single range measurement and return the result in mm.
    Returns distance in mm or -1 if measurement failed.
    """
    try:
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
                raise RuntimeError("Timeout waiting for VL53L0X measurement")
            time.sleep(0.01)
        
        # Read distance
        data = read_block_data(REG_RESULT_RANGE_STATUS, 12)
        range_mm = (data[10] << 8) | data[11]
        
        return range_mm
    except Exception as e:
        print(f"Error getting distance: {e}")
        return -1

def cleanup_sensor():
    """Clean up the I2C bus."""
    global bus
    if bus is not None:
        bus.close()
        bus = None
        print("VL53L0X sensor cleaned up")