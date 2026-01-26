# Lab 2 - Part 3.8 Publisher

import paho.mqtt.client as paho
import time
import threading
import pickle
from gpiozero import DistanceSensor, LED

# Configuration Parameters
MQTT_BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "jpor/asn2"
PUBLISH_INTERVAL = 1  # 1 Hz

# GPIO Pin Setup
sensor = DistanceSensor(echo=24, trigger=23)
led = LED(22)

# Event to signal when connected
connected_event = threading.Event()

# MQTT on_connect callback
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Publisher connected with code {reason_code}.")
    connected_event.set()

# MQTT Client Setup
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, 
    client_id="publisher_node", 
    protocol=paho.MQTTv5
)
client.on_connect = on_connect

# Establish connection
client.connect(MQTT_BROKER, PORT)
client.loop_start()

# Wait for connection to be established
connected_event.wait()

try:
    print("Publisher is running. Sending Distance data...")
    while True:
        # gpiozero returns distance in meters, multiplying by 100 for cm
        distance_cm = round(sensor.distance * 100, 2)
        
        # Local feedback: LED turns on if object is closer than 5cm
        if distance_cm < 5:
            led.on()
        else:
            led.off()

        # Publish the numeric distance
        payload_bytes = pickle.dumps(distance_cm)
        client.publish(TOPIC, payload_bytes)
        
        print(f"Published: {distance_cm} cm")
        time.sleep(PUBLISH_INTERVAL)

except KeyboardInterrupt:
    print("\nStopping Publisher...")

client.loop_stop()
client.disconnect()