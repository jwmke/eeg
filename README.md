# ADS 1299 Affordable EEG PCB

### An 8-channel EEG Pi Pico W shield, based off of OpenBCI's [Cyton Biosensing Board](https://shop.openbci.com/products/cyton-biosensing-board-8-channel), for 1/10th the price.

![image](https://github.com/user-attachments/assets/7f82fe20-6b87-4119-bc05-a45672c2349d)

## Instructions
1. Update your SSID and PASSWORD in the pico/main.py file
2. Upload the main.py to the Pi Pico W
3. Run the pico/main.py on the Pico Pi W and note the printed IP
5. Unplug the Pi Pico W from the PC and place it into the PCB
6. Update the PICO_IP in the computer/plot_data.py file
7. Run the computer/plot_data.py on a PC
8. Plug a 3.7V Lipo battery into the PCB
9. Blinking LED == Connecting, Solid LED == Succesfully streaming to PC

## Schematics

![image](https://github.com/user-attachments/assets/e2b672db-bf7a-486a-9f5a-fc39cb14f0e8)

![image](https://github.com/user-attachments/assets/07098f14-90e2-464e-b14d-20471145e994)

![image](https://github.com/user-attachments/assets/d9d8564d-83bc-4e86-8cc9-23578211d24b)

![image](https://github.com/user-attachments/assets/fbfae927-83b5-4a3a-8079-c9279520f184)

![image](https://github.com/user-attachments/assets/7d1640ee-7fc7-4d7d-9f45-8f52d8cfaa22)

![image](https://github.com/user-attachments/assets/45b6a96c-68d1-4d47-97d6-e77dfcc51c82)

![image](https://github.com/user-attachments/assets/0251fa35-c0b8-45d9-b5da-b29179068f7d)

![image](https://github.com/user-attachments/assets/3a47b5a8-f7fc-47e9-b7a3-08461ea7b4df)

![image](https://github.com/user-attachments/assets/a65c8b84-e897-4ac7-92bd-e772d139bad6)

![image](https://github.com/user-attachments/assets/390a372e-a838-4f77-870a-e818f4891f6f)

## Layout

Top

![image](https://github.com/user-attachments/assets/80041890-a3dc-42fe-8db9-fd0bfd1d4769)

Bottom

![image](https://github.com/user-attachments/assets/e9177a21-83ea-44e6-ae28-dec9ab12bd8a)

Ground

![image](https://github.com/user-attachments/assets/2c11d5c2-dc31-4e52-be85-cb2173332824)

AVSS/-2.5V

![image](https://github.com/user-attachments/assets/47b8ce07-fdc6-4df2-93f3-ab50272ebdfa)
