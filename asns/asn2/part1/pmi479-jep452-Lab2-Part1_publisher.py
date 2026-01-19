import paho.mqtt.client as paho
import time
import threading
import pickle

payload = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

connected_event = threading.Event()

client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5
)


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"CONNACK received with code {reason_code}.")
    connected_event.set()


client.on_connect = on_connect

mqttBroker = "broker.mqttdashboard.com"
port = 1883

client.connect(mqttBroker, port)
client.loop_start()

# Wait for connection to be established
connected_event.wait()

try:
    count = 0
    while True:
        payload_bytes = pickle.dumps(payload)
        result = client.publish("jpor/asn2", payload_bytes)
        result.wait_for_publish()
        print(f"Published '{payload}' to jpor/asn2")
        count += 1
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")

client.loop_stop()
client.disconnect()
