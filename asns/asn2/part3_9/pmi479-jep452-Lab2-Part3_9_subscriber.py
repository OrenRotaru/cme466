# Lab 2 - Part 3.9 Subscriber

import paho.mqtt.client as paho
import pickle
from gpiozero import LED

# Configuration Parameters
MQTT_BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "jpor/asn2"

# Hardware Setup
led = LED(22)

# MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with code {reason_code}.")
    client.subscribe(TOPIC)

# Message callback
def on_message(client, userdata, msg):
    try:
        payload = pickle.loads(msg.payload)
        # Control LED based on the message typed in the publisher
        if payload == "on":
            led.on()
            print("Received: ON")
        elif payload == "off":
            led.off()
            print("Received: OFF")
        else:
            print(f"Received unknown command: {payload}")
    except Exception as e:
        print(f"Error decoding: {e}")

# MQTT Client Setup
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, 
    client_id="subscriber_node", 
    userdata=None, 
    protocol=paho.MQTTv5
)
# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to Broker
client.connect(MQTT_BROKER, PORT)

# Main loop
try:
    client.loop_forever()
except KeyboardInterrupt:
    led.off()
    print("\nDisconnecting...")
    client.disconnect()