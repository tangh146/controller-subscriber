import rotary_encoder
import pigpio
from time import sleep

# These are the GPIO pin numbers for your encoder.
#Use the BCM numbers, not the Board number for these variables.
channel_A = 17 # Using GPIO17
channel_B = 27 # Using GPIO4

position = 0 # The current position of the encoder - default to zero at program start.
old_position = 0 # The previous position of the encoder - used to skip writing to the console
# unless the position has changed.

def callback(way): # Updates the position with the direction the encoder was turned.
    global position
    position += way

pi = pigpio.pi() # Defines the specfic Raspberry Pi we are polling for information - defaults to the local device.
decoder = rotary_encoder.decoder(pi, channel_A, channel_B, callback) # Creates an object that automatically fires

while True: # Only prints the position of the encoder if a change has been made, refreshing every millisecond.
            # Helps reduce lag when moving a high resolution encoder extremely quickly.
            # Interstingly, the system didn't lose counts for me, but it did take an inordinate amount of time
            # to catch up when wiriting to the console.       
    if position != old_position:
        print("pos = {}".format(position))
        old_position = position
        sleep(0.001)
