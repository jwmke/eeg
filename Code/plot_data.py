import serial
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import time

# Configure serial port (adjust COM port as needed)
ser = serial.Serial('COM5', 115200, timeout=1)

# Initialize plots
plt.ion()
fig, axs = plt.subplots(8, 1, figsize=(10, 12))
fig.suptitle('EEG Channels')

# Buffer for each channel
BUFFER_SIZE = 500
buffers = [deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE) for _ in range(8)]
lines = []

# Setup each subplot
for i, ax in enumerate(axs):
    line, = ax.plot(range(BUFFER_SIZE), [0]*BUFFER_SIZE)
    lines.append(line)
    ax.set_ylabel(f'Ch{i+1} (µV)')
    ax.grid(True)
    ax.set_ylim(-100, 100)  # Adjust as needed

axs[-1].set_xlabel('Samples')
plt.tight_layout()

try:
    while True:
        if ser.in_waiting:
            # Read and parse data
            line = ser.readline().decode().strip()
            try:
                # Convert string of comma-separated values to float list
                data = [float(x) for x in line.split(',')]
                if len(data) == 8:  # Ensure we have all 8 channels
                    # Update buffers and plot
                    for i, value in enumerate(data):
                        buffers[i].append(value)
                        lines[i].set_ydata(list(buffers[i]))
                    
                    fig.canvas.draw()
                    fig.canvas.flush_events()
            except ValueError:
                continue
            
except KeyboardInterrupt:
    ser.close()
    plt.close()