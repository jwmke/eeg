from machine import Pin
import time

try:
    # For Pico W
    led = Pin("LED", Pin.OUT)
except:
    # For original Pico
    led = Pin(25, Pin.OUT)

try:
    print("LED blinking started! Press Ctrl+C to stop.")
    while True:
        led.toggle()      # Switch LED state
        time.sleep(0.5)   # Wait for 500ms
        
except KeyboardInterrupt:
    # Turn off LED when program is interrupted
    led.value(0)
    print("\nProgram stopped by user")