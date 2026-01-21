import paho.mqtt.client as paho
import pickle
import threading

# MQTT Client Setup
connected_event = threading.Event()

# MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"CONNACK received with code {reason_code}.")
    connected_event.set()

# MQTT Client Initialization
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5
)
client.on_connect = on_connect

# Connect to Broker
mqttBroker = "broker.mqttdashboard.com"
client.connect(mqttBroker, 1883)
client.loop_start()

connected_event.wait()

try:
    # Publish messages based on user input in terminal
    while True:
        cmd = input("Enter 'on', 'off', or 'exit': ").strip().lower()
        if cmd == 'exit': # exit breaks and stops the program
            break
        if cmd in ['on', 'off']:
            payload_bytes = pickle.dumps(cmd)
            client.publish("jpor/asn2", payload_bytes)
except KeyboardInterrupt:
    print("\nStopping...")

client.loop_stop()
client.disconnect()