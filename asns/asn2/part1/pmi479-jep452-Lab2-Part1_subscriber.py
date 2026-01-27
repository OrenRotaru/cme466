# PMI479 - Lab 2 - Part 1 Subscriber

import paho.mqtt.client as paho
import pickle

# Configuration Parameters
MQTT_BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "jpor/asn2"

# Callback Functions
# Callback which deserializes the payload and prints the second element if it's an array
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with code {reason_code}.")
    client.subscribe(TOPIC)
    print(f"Subscribed to {TOPIC}. Waiting for messages... (Ctrl+C to stop)")

def on_message(client, userdata, msg):
    # Deserialize the data
    received_data = pickle.loads(msg.payload)
    
    # Part 1, Q2: Show the data type of the received message
    print("-" * 35)
    print(f"Received Message: {received_data}")
    print(f"Message Data Type: {type(received_data)}")

    # Part 1, Q3: Type conversion, Arithmetic, Logical operation
    if isinstance(received_data, list):
        # 3(c): Print a selected set of data (from index 1)
        print(f"c) - Selected Data (Index 1): {received_data[1]}")

        # 3(a): Change the data type (Casting int to float or string)
        type_change = str(received_data[2])
        print(f"a) - Data type change: Element 2 converted to {type(type_change)}")

        # 3(b): Perform arithmetic operation by squaring the sixth element
        math_result = received_data[5] ** 2
        print(f"b) - Arithmetic Result (Element 5 squared): {math_result}")
        # 3(b): Logical operation
        if received_data[9] > 5:
            print(f"b) - Logical Result: Element 9: {received_data[9]} received_data[9] > 5:")
    else:
        print("Data Recieved not in list format.")

# Create MQTT client instance
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, 
    client_id="subscriber_node", 
    userdata=None, 
    protocol=paho.MQTTv5
)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(MQTT_BROKER, PORT)

try:
    # loop_forever to keep the subscriber running until interrupted
    client.loop_forever()
# Handle safe shutdown on ctrl+C interrupt
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()