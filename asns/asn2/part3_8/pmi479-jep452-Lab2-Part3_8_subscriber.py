# Lab 2 - Part 3.8 Subscriber

import paho.mqtt.client as paho
import pickle

# Configuration Parameters
MQTT_BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "jpor/asn2"

# MQTT on_connect callback
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Subscriber connected with code {reason_code}.")
    # Subscribe to the topic upon connection
    client.subscribe(TOPIC)

# MQTT on_message callback
def on_message(client, userdata, msg):
    try:
        payload = pickle.loads(msg.payload)
        
        # Check if the message is a distance (float/int)
        if isinstance(payload, (float, int)):
            print(f"Live Sensor Data: {payload} cm")
        else:
            print(f"Received other data: {payload}")
            
    except Exception as e:
        print(f"Error decoding: {e}")

# MQTT Client Setup
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, 
    client_id="subscriber_node", 
    protocol=paho.MQTTv5
)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT Broker
client.connect(MQTT_BROKER, PORT)

# Main loop
try:
    print("Subscriber waiting for live sensor updates...")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()