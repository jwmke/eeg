from machine import Pin, SPI
import time
import struct

class ADS1299:
    def __init__(self):
        # Pin Definitions
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

    def start_acquisition(self):
        """Start continuous data acquisition"""
        self.send_command(0x10)  # RDATAC
        self.start.value(1)
        
        try:
            while True:
                data = self.read_data_sample()
                # Convert data to string and print
                data_str = ",".join([f"{x:.2f}" for x in data])
                print(data_str)
                time.sleep_ms(4)  # Small delay to maintain ~250 SPS
                
        except KeyboardInterrupt:
            self.start.value(0)
            self.send_command(0x11)  # SDATAC

# Main execution
if __name__ == '__main__':
    ads = ADS1299()
    ads.init_device()
    print("Starting data acquisition... Press Ctrl+C to stop.")
    ads.start_acquisition()