import network
import socket
from machine import Pin, SPI
import time
import json

# WiFi credentials
SSID = ''
PASSWORD = ''

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

class SoftSPI:
    def __init__(self, sck, mosi, miso, baudrate=1000000):
        self.sck = sck
        self.sck.init(Pin.OUT, value=0)
        
        self.mosi = mosi
        self.mosi.init(Pin.OUT, value=0)
        
        self.miso = miso
        self.miso.init(Pin.IN)
        
        # SPI Mode 1: CPOL=0, CPHA=1
        self.sck.value(0)  # Ensure clock starts low

    def write(self, data):
        for b in data:
            # Delay before byte transmission
            time.sleep_us(10)
            
            for i in range(8):
                self.mosi.value((b >> (7-i)) & 1)  # Set data
                time.sleep_us(5)  # Setup time
                self.sck.value(1)  # Clock high
                time.sleep_us(5)  # Hold time
                self.sck.value(0)  # Clock low
                time.sleep_us(5)  # Inter-bit delay
            
            # Inter-byte delay
            time.sleep_us(10)

    def readinto(self, buf):
        for i in range(len(buf)):
            byte = 0
            # Delay before byte reception
            time.sleep_us(10)
            
            for j in range(8):
                self.sck.value(1)  # Clock high
                time.sleep_us(5)   # Setup time
                bit = self.miso.value()
                byte = (byte << 1) | bit
                time.sleep_us(5)   # Hold time
                self.sck.value(0)  # Clock low
                time.sleep_us(5)   # Inter-bit delay
            
            buf[i] = byte
            # Inter-byte delay
            time.sleep_us(10)

class ADS1299:
    def __init__(self):
        # GPIO setup with forced output mode
        self.cs = Pin(2, Pin.OUT)    
        self.cs.on()  # Set high (inactive)
        
        self.start = Pin(7, Pin.OUT)
        self.start.off()  # Start low
        
        self.reset = Pin(9, Pin.OUT)
        self.reset.on()   # Start high
        
        self.pwdn = Pin(11, Pin.OUT)
        self.pwdn.on()    # Start high (powered on)
        
        self.drdy = Pin(6, Pin.IN)   # DRDY as input

        # Setup SPI pins with forced values
        self.sck = Pin(4, Pin.OUT)
        self.mosi = Pin(1, Pin.OUT)
        self.miso = Pin(5, Pin.IN)
        
        # Force initial states
        self.sck.off()    # Clock starts low
        self.mosi.off()   # MOSI starts low
        
        # Initialize Software SPI
        self.spi = SoftSPI(sck=self.sck, mosi=self.mosi, miso=self.miso)

            
    def write_reg(self, reg, data):
        """Write data to a register"""
        print(f"Writing register {hex(reg)} with value {hex(data)}")
        self.cs.value(1)
        time.sleep_ms(1)  # Longer delay
        self.cs.value(0)
        time.sleep_ms(1)  # Longer delay
        
        # Send write command
        self.spi.write(bytes([0x40 | reg]))
        time.sleep_ms(1)  # Longer delay
        
        # Send number of registers to write minus 1
        self.spi.write(bytes([0x00]))
        time.sleep_ms(1)  # Longer delay
        
        # Send data
        self.spi.write(bytes([data]))
        time.sleep_ms(1)  # Longer delay
        
        self.cs.value(1)
        time.sleep_ms(1)  # Longer delay

    def read_reg(self, reg):
        """Read from a register"""
        self.cs.value(1)  # Ensure CS is high initially
        time.sleep_us(2)
        self.cs.value(0)  # Pull CS low to start transaction
        time.sleep_us(2)
        self.spi.write(bytes([0x20 | reg]))  # Read command
        time.sleep_us(2)
        self.spi.write(bytes([0x00]))        # Number of registers to read
        time.sleep_us(2)
        result = bytearray(1)
        self.spi.readinto(result)
        time.sleep_us(2)
        self.cs.value(1)  # Pull CS high to end transaction
        time.sleep_us(2)
        return result[0]

    def send_command(self, cmd):
        """Send a command to ADS1299"""
        self.cs.value(1)  # Ensure CS is high initially
        time.sleep_us(2)
        self.cs.value(0)  # Pull CS low to start transaction
        time.sleep_us(2)
        self.spi.write(bytes([cmd]))
        time.sleep_us(2)
        self.cs.value(1)  # Pull CS high to end transaction
        time.sleep_us(2)
    
    def verify_communication(self):
        """Verify SPI communication"""
        print("Verifying SPI communication...")
        
        # Write a test pattern to CONFIG2 register
        test_value = 0xD0  # A value we haven't used yet
        print(f"Writing test value {hex(test_value)} to CONFIG2")
        self.write_reg(0x02, test_value)
        
        # Read back the value
        time.sleep_ms(10)
        readback = self.read_reg(0x02)
        print(f"Read back value: {hex(readback)}")
        
        if readback == test_value:
            print("SPI communication verified!")
            return True
        else:
            print("SPI communication failed!")
            return False

    def init_device(self):
        """Initialize the ADS1299"""
        print("Starting device initialization...")
        
        # Power up sequence
        print("Power down")
        self.pwdn.value(0)
        time.sleep_ms(100)
        print("Power up")
        self.pwdn.value(1)
        time.sleep_ms(100)
        
        # Reset sequence
        print("Start reset sequence")
        self.reset.value(1)
        time.sleep_ms(100)
        print("Reset low")
        self.reset.value(0)
        time.sleep_ms(100)
        print("Reset high")
        self.reset.value(1)
        time.sleep_ms(100)
        
        # Send SDATAC command
        print("Sending SDATAC command")
        self.send_command(0x11)
        time.sleep_ms(10)
        
        # Verify communication
        if not self.verify_communication():
            raise RuntimeError("Failed to establish SPI communication")
        
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
            
            # Debug print raw bytes
            print(f"Ch{i+1} raw bytes: {hex(raw_data[start_idx])} {hex(raw_data[start_idx + 1])} {hex(raw_data[start_idx + 2])}")
            
            # Convert to signed value
            if channel_data & 0x800000:
                channel_data |= ~0xFFFFFF
            
            # Debug print before voltage conversion
            print(f"Ch{i+1} value before conversion: {channel_data}")
            
            # Convert to microvolts
            voltage = (channel_data * 4.5 * 1000000) / (24 * 8388607)
            print(f"Ch{i+1} voltage: {voltage} µV")
            channels_data.append(voltage)
        
        #print("Raw channel data:", channels_data)  # Debug print
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
