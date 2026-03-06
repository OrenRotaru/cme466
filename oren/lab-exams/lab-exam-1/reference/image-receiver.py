import paho.mqtt.client as mqtt
import time

BROKER = "test.mosquitto.org"
TOPIC = "lab/camera/image"
OUTPUT_FILENAME = "received_image.jpg"

def on_connect(client, userdata, flags, rc, properties=None): # Updated callback signature for v2
    if rc == 0:
        print(f"Connected to Broker. Waiting for image on {TOPIC}...")
        client.subscribe(TOPIC)
    else:
        print("Connection failed")

def on_message(client, userdata, message):
    print(f"Message received! Payload size: {len(message.payload)} bytes")
    
    # 1. Open a file for the image in binary write mode ('wb') 
    with open(OUTPUT_FILENAME, 'wb') as f:
        # 2. Write the received bytes to the file 
        f.write(message.payload)
        
    print(f"Image saved as {OUTPUT_FILENAME}")
    # We disconnect after receiving one image for this test
    client.disconnect()

# Setup Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)

# Loop forever until we receive the image
client.loop_forever()