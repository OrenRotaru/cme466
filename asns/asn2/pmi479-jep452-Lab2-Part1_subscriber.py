import paho.mqtt.client as paho
import pickle


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with code {reason_code}.")
    client.subscribe("jpor/asn2")
    print("Subscribed to jpor/asn2. Waiting for messages... (Ctrl+C to stop)")


def on_message(client, userdata, msg):
    payload = pickle.loads(msg.payload)
    print(f"Received: {payload} on topic {msg.topic}")
    # if its an array can, access the second element
    if isinstance(payload, list):
        print(f"Second element: {payload[1]}")
    else:
        print(f"Payload is not a list: {payload}")


client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5
)
client.on_connect = on_connect
client.on_message = on_message

mqttBroker = "broker.mqttdashboard.com"
port = 1883

client.connect(mqttBroker, port)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()
