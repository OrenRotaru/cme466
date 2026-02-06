import paho.mqtt.client as mqtt
import time
import os

BROKER = "test.mosquitto.org"
TOPIC = "lab/camera/image"
INPUT_FILENAME = "my_photo.jpg" # Ensure this file exists!

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)

try:
    print(f"Reading {INPUT_FILENAME}...")
    
    # 1. Open image in binary read format [cite: 460]
    with open(INPUT_FILENAME, 'rb') as file:
        filecontent = file.read()
        
        # 2. Convert to byte array [cite: 463]
        byteArr = bytearray(filecontent)
        
        print(f"Image size: {len(byteArr)} bytes")
        
        # 3. Publish the byte array [cite: 466]
        client.publish(TOPIC, byteArr)
        print(f"Published image to {TOPIC}")

except FileNotFoundError:
    print(f"Error: Please place a file named '{INPUT_FILENAME}' in this directory.")

# brief pause to ensure message is sent before script exits
time.sleep(2)
client.disconnect()