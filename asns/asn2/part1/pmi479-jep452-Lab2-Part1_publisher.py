# PMI479 - Lab 2 - Part 1 Publisher

import paho.mqtt.client as paho
import time
import threading
import pickle

# Configuration Parameters
MQTT_BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "jpor/asn2"
QOS_LEVEL = 1      # Part 1, Q4(a): Setting QoS
RETAIN_MSG = True  # Part 1, Q4(b): Setting Retain Flag
PAYLOAD = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Event to signal connection establishment
connected_event = threading.Event()

# Callback which sets the connected event upon connection
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"CONNACK received with code {reason_code}.")
    connected_event.set()

# Create MQTT client instance
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, 
    client_id="publisher_node", 
    userdata=None, 
    protocol=paho.MQTTv5
)
client.on_connect = on_connect

# Connect to the broker and start the loop
client.connect(MQTT_BROKER, PORT)
client.loop_start()

# Wait for connection to be established
connected_event.wait()

try:
    # Publishing loop
    while True:
        payload_bytes = pickle.dumps(PAYLOAD)
        
        print(f"Publishing to {TOPIC} | QoS: {QOS_LEVEL} | Retain: {RETAIN_MSG}")
        
        # Part 1, Q4(a) & Q4(b): Publish with QoS and Retain flag
        # Setting payload=None would clear the retained message
        result = client.publish(TOPIC, payload_bytes, qos=QOS_LEVEL, retain=RETAIN_MSG)
        result.wait_for_publish()
        
        print(f"Published '{PAYLOAD}' to {TOPIC}")
        time.sleep(5)

# Handle safe shutdown on ctrl+C interrupt
except KeyboardInterrupt:
    print("\nStopping...")

# Stop the loop and disconnect
client.loop_stop()
client.disconnect()


# import paho.mqtt.client as paho
# import time
# import threading
# import pickle

# payload = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# connected_event = threading.Event()

# client = paho.Client(
#     paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5
# )

# # Callback which sets the connected event upon connection
# def on_connect(client, userdata, flags, reason_code, properties):
#     print(f"CONNACK received with code {reason_code}.")
#     connected_event.set()


# client.on_connect = on_connect

# mqttBroker = "broker.mqttdashboard.com"
# port = 1883

# client.connect(mqttBroker, port)
# client.loop_start()

# # Wait for connection to be established
# connected_event.wait()

# try:
#     count = 0
#     while True:
#         payload_bytes = pickle.dumps(payload)
#         print(f"Publishing '{payload_bytes}' to jpor/asn2")
#         result = client.publish("jpor/asn2", payload_bytes)
#         result.wait_for_publish()
#         print(f"Published '{payload}' to jpor/asn2")
#         count += 1
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("\nStopping...")

# client.loop_stop()
# client.disconnect()
