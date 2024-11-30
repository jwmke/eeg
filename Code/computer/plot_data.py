import socket
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import time

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

# Modify these in your plot_data.py
BUFFER_SIZE = 100  # Reduced from 500
UPDATE_INTERVAL = 0.1  # Update every 100ms

# Buffer for each channel
buffers = [deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE) for _ in range(8)]
lines = []

# Setup each subplot
for i, ax in enumerate(axs):
    line, = ax.plot(range(BUFFER_SIZE), [0]*BUFFER_SIZE)
    lines.append(line)
    ax.set_ylabel(f'Ch{i+1} (µV)')
    ax.grid(True)
    ax.set_ylim(-500, 500)  # Increased range

last_update = time.time()

try:
    sock = connect_to_pico()
    buffer = ""
    
    while True:
        data = sock.recv(1024).decode()
        buffer += data
        
        current_time = time.time()
        
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            try:
                data_dict = json.loads(line)
                channel_data = data_dict['channels']
                
                # Update buffers
                for i, value in enumerate(channel_data):
                    buffers[i].append(value)
                
                # Only update plot periodically
                if current_time - last_update > UPDATE_INTERVAL:
                    for i in range(8):
                        lines[i].set_ydata(list(buffers[i]))
                    
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    last_update = current_time
                    
            except json.JSONDecodeError:
                continue
            
except KeyboardInterrupt:
    sock.close()
    plt.close()