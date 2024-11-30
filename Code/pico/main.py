import network
import socket
from machine import Pin, SPI
import time
import json

# WiFi credentials
SSID = 'OpenWrt'
PASSWORD = 'DoH3rocks'

# Setup LED
try:
    led = Pin("LED", Pin.OUT)
except:
    led = Pin(25, Pin.OUT)

def blink_led():
    """Toggle LED state"""
    led.toggle()

def set_led_on():
    """Turn LED on solid"""
    led.value(1)

def set_led_off():
    """Turn LED off"""
    led.value(0)

def connect_wifi():
    """Connect to WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    # Wait for connection, blinking LED while trying
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        blink_led()
        time.sleep(0.5)
        blink_led()
        time.sleep(0.5)
    
    if wlan.status() != 3:
        # Connection failed - keep LED blinking
        raise RuntimeError('WiFi connection failed')
    else:
        # Connection successful - LED solid
        set_led_on()
        print('Connected')
        status = wlan.ifconfig()
        print('IP:', status[0])
    return status[0]  # Return IP address

class ADS1299:
    def __init__(self):
        self.cs = Pin(2, Pin.OUT, value=1)      # Chip Select
        self.start = Pin(7, Pin.OUT)            # Start Conversion
        self.reset = Pin(9, Pin.OUT)            # Reset
        self.pwdn = Pin(11, Pin.OUT)            # Power Down
        self.drdy = Pin(6, Pin.IN)              # Data Ready
        
        # Initialize SPI
        self.spi = SPI(0,
                      baudrate=1_000_000,
                      polarity=0,
                      phase=1,
                      bits=8,
                      firstbit=SPI.MSB)
    
    def write_reg(self, reg, data):
        """Write data to a register"""
        self.cs.value(0)
        self.spi.write(bytes([0x40 | reg, 0x00, data]))
        self.cs.value(1)
        time.sleep_us(2)
        
    def send_command(self, cmd):
        """Send a command to ADS1299"""
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)
        time.sleep_us(2)
    
    def init_device(self):
        """Initialize the ADS1299"""
        # Power up sequence
        self.pwdn.value(1)
        time.sleep_ms(100)
        
        # Reset the device
        self.reset.value(0)
        time.sleep_ms(1)
        self.reset.value(1)
        time.sleep_ms(100)
        
        # Send initial commands
        self.send_command(0x11)  # SDATAC
        time.sleep_ms(10)
        
        # Configure registers
        self.write_reg(0x01, 0x96)  # CONFIG1: 250 SPS
        self.write_reg(0x02, 0xC0)  # CONFIG2: Internal test signal disabled
        self.write_reg(0x03, 0xE0)  # CONFIG3: Enable internal reference buffer

        # Configure all channels for normal operation with gain=24
        for reg in range(0x05, 0x0D):  # CH1SET to CH8SET
            self.write_reg(reg, 0x60)   # Normal operation, gain=24
        
        time.sleep_ms(10)
        
    def start_acquisition(self, sock):
        """Start continuous data acquisition and send over WiFi"""
        self.send_command(0x10)  # RDATAC
        self.start.value(1)
        
        try:
            while True:
                data = self.read_data_sample()
                # Convert data to JSON string
                data_json = json.dumps({'channels': data})
                sock.send(data_json.encode() + b'\n')
                time.sleep_ms(4)  # Maintain ~250 SPS
                
        except Exception as e:
            print(f"Error: {e}")
            self.start.value(0)
            self.send_command(0x11)  # SDATAC
            # If connection is lost, start blinking LED
            while True:
                blink_led()
                time.sleep(0.5)
    
    def read_data_sample(self):
        """Read one sample from all channels"""
        while self.drdy.value():
            pass
            
        self.cs.value(0)
        
        # Read 27 bytes (status + 8 channels)
        raw_data = bytearray(27)
        self.spi.readinto(raw_data)
        
        self.cs.value(1)
        
        # Parse the data
        channels_data = []
        for i in range(8):
            start_idx = 3 + (i * 3)
            channel_data = (raw_data[start_idx] << 16) | (raw_data[start_idx + 1] << 8) | raw_data[start_idx + 2]
            
            # Convert to signed value
            if channel_data & 0x800000:
                channel_data |= ~0xFFFFFF
            
            # Convert to microvolts
            voltage = (channel_data * 4.5 * 1000000) / (24 * 8388607)
            channels_data.append(voltage)
            
        return channels_data

# Main execution
def main():
    try:
        # Start with LED blinking
        set_led_off()
        
        # Connect to WiFi
        ip = connect_wifi()
        
        # Setup Socket Server
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(1)
        
        print('Ready for connection')
        
        # Initialize ADS1299
        ads = ADS1299()
        ads.init_device()
        
        while True:
            cl, addr = s.accept()
            print('Client connected from', addr)
            set_led_on()  # Solid LED when client connected
            ads.start_acquisition(cl)
            cl.close()
            # If we get here, connection was lost
            set_led_off()
            
    except KeyboardInterrupt:
        set_led_off()
    except Exception as e:
        print(f"Error: {e}")
        # Error occurred, blink LED continuously
        while True:
            blink_led()
            time.sleep(0.5)

if __name__ == '__main__':
    main()
