import socket
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# Connect to Pico W
PICO_IP = '192.168.42.117'
PORT = 80

def connect_to_pico():
    s = socket.socket()
    s.connect((PICO_IP, PORT))
    return s

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
    ax.set_ylim(-100, 100)

axs[-1].set_xlabel('Samples')
plt.tight_layout()

try:
    sock = connect_to_pico()
    buffer = ""
    
    while True:
        data = sock.recv(1024).decode()
        buffer += data
        
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            try:
                data_dict = json.loads(line)
                channel_data = data_dict['channels']
                
                # Update buffers and plot
                for i, value in enumerate(channel_data):
                    buffers[i].append(value)
                    lines[i].set_ydata(list(buffers[i]))
                
                fig.canvas.draw()
                fig.canvas.flush_events()
                
            except json.JSONDecodeError:
                continue
            
except KeyboardInterrupt:
    sock.close()
    plt.close()